"""Telegram adapter.

Responsibilities:
- Translate Telegram updates into application commands and return responses.
- Compose and inject infrastructure implementations into use cases.

Constraints:
- No domain logic. No direct ORM/SQL here (beyond calling init at startup).
"""

import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.application.track import IngestTrackCommand, IngestTrackUseCase
from app.application.user import UpsertTelegramUserUseCase
from app.infrastructure.db.postgres import get_session, init_db
from app.infrastructure.format_detector import SimpleFormatDetector
from app.infrastructure.id_gen import UUIDGen
from app.infrastructure.parsers.parser_impl import TrackParserImpl, TrackFeatureExtractorImpl
from app.infrastructure.repos.track_repo_sql import TrackMetadataRepoSQL, TrackFeaturesRepoSQL
from app.infrastructure.repos.user_repo_sql import UserRepoSQL
from app.infrastructure.storage_local import LocalFSStorage

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
parser = TrackParserImpl()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Пришли мне GPX/FIT файл — позже я его разберу."
    )


async def handle_document(update, context):
    doc = update.message.document
    file = await context.bot.get_file(doc.file_id)
    blob = await file.download_as_bytearray()
    user = update.effective_user

    with get_session() as s:
        user_id = UpsertTelegramUserUseCase(UserRepoSQL(s)).execute(user)

        usecase = IngestTrackUseCase(
            storage=LocalFSStorage("./data/uploads"),
            id_gen=UUIDGen(),
            detector=SimpleFormatDetector(),
            parser=parser,
            meta_repo=TrackMetadataRepoSQL(s),
            feature_extractor=TrackFeatureExtractorImpl(),
            features_repo=TrackFeaturesRepoSQL(s), 
        )
        row = usecase.execute(
            IngestTrackCommand(
                user_id=user_id,
                filename=doc.file_name or "unknown",
                blob=bytes(blob),
                source="telegram",
            )
        )
    await update.message.reply_text(
        "✅ Сохранено: {filename} ({format})\n"
        "Дистанция: {distance} км, Длительность: {duration} c, Набор: {gain} м\n"
        "ID: {tid}".format(
            filename=row.get("filename"),
            format=row.get("format"),
            distance=(row.get("distance_km")),
            duration=(row.get("duration_s")),
            gain=(row.get("elevation_gain_m")),
            tid=row.get("id"),
        )
    )


def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.COMMAND, start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()


if __name__ == "__main__":
    main()
