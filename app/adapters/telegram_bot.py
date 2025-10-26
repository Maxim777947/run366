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
    await update.message.reply_text(
        f"✅ Сохранено: {row.filename} ({row.format})\n"
        f"Дистанция: {row.distance_km} км, Длительность: {row.duration_s} c, Набор: {row.elevation_gain_m} м\n"
        f"ID: {row.id}"
    )


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.COMMAND, start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()


if __name__ == "__main__":
    main()
