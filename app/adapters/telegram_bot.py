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
    MessageHandler,
    filters,
    ContextTypes,
)
from app.infrastructure.parsers.parser_impl import TrackParserImpl
from app.infrastructure.db.postgres import get_session, init_db
from app.application.usecases_ingest import IngestTrackUseCase, IngestTrackCommand
from app.infrastructure.storage_local import LocalFSStorage
from app.infrastructure.id_gen import UUIDGen
from app.infrastructure.format_detector import SimpleFormatDetector
from app.infrastructure.repos.track_metadata_repo_sql import TrackMetadataRepoSQL


load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Пришли мне GPX/FIT файл — позже я его разберу."
    )


parser = TrackParserImpl()


async def handle_document(update, context):
    doc = update.message.document
    file = await context.bot.get_file(doc.file_id)
    blob = await file.download_as_bytearray()

    with get_session() as s:
        usecase = IngestTrackUseCase(
            storage=LocalFSStorage("./data/uploads"),
            id_gen=UUIDGen(),
            detector=SimpleFormatDetector(),
            parser=parser,
            meta_repo=TrackMetadataRepoSQL(s),
        )
        row = usecase.execute(
            IngestTrackCommand(
                user_id=update.effective_user.id,
                filename=doc.file_name or "unknown",
                blob=bytes(blob),
                source="telegram",
            )
        )
        print(row)
    await update.message.reply_text(
        "✅ Сохранено: {filename} ({format})\n"
        "Дистанция: {distance} км, Длительность: {duration} c, Набор: {gain} м\n"
        "ID: {tid}".format(
            filename=row.get("filename"),
            format=row.get("format"),
            distance=(row.get("distance_km") or 0),
            duration=(row.get("duration_s") or 0),
            gain=(row.get("elevation_gain_m") or 0),
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
