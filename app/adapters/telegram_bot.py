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
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.application.track import (
    ComputeAndIndexTrackFeaturesUseCase,
    IngestTrackCommand,
    IngestTrackUseCase,
    RecommendRoutesUseCase,
)
from app.application.user import UpsertTelegramUserUseCase
from app.domain.models.track import ComputeAndIndexTrackFeaturesCommand, RecommendRoutesCommand, TrackFormat
from app.infrastructure.db.postgres import get_session, init_db
from app.infrastructure.db.qdrant import init_qdrant
from app.infrastructure.parsers.parser_impl import TrackFeatureExtractorImpl, TrackParserImpl
from app.infrastructure.repos.track_repo_qdrant import TrackVectorIndexQdrant
from app.infrastructure.repos.track_repo_sql import (
    LocalFSStorage,
    SimpleFormatDetector,
    TrackFeaturesRepoSQL,
    TrackMetadataRepoSQL,
    UUIDGen,
)
from app.infrastructure.repos.user_repo_sql import UserRepoSQL
from app.infrastructure.vectorize.track import HandcraftedTrackVectorizer

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
parser = TrackParserImpl()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли мне GPX/FIT файл — позже я его разберу.")


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
        features_use_case = ComputeAndIndexTrackFeaturesUseCase(
            feature_extractor=TrackFeatureExtractorImpl(),
            features_repository=TrackFeaturesRepoSQL(s),
            vector_index=TrackVectorIndexQdrant(),
            track_vectorizer=HandcraftedTrackVectorizer(),
        )
        features_use_case.execute(
            ComputeAndIndexTrackFeaturesCommand(
                track_id=row["id"],
                track_format=TrackFormat(row["format"]),
                file_bytes=bytes(blob),
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


async def handle_recommend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /recommend."""
    user = update.effective_user

    with get_session() as s:
        use_case = RecommendRoutesUseCase(
            user_repo=UserRepoSQL(s),
            features_repo=TrackFeaturesRepoSQL(s),
            vectorizer=HandcraftedTrackVectorizer(),
            vector_index=TrackVectorIndexQdrant(),
        )

        # Выполняем команду (передаём только tg_id!)
        recommendations = use_case.execute(
            RecommendRoutesCommand(
                tg_id=user.id,
                top_k=3,
                include_other_users=True,
            )
        )

        if not recommendations:
            await update.message.reply_text("🤷‍♂️ Пока нет данных для рекомендаций.\nЗагрузите больше треков!")
            return
        # Форматируем ответ
        response = "🎯 **Рекомендованные маршруты:**\n\n"
        for i, rec in enumerate(recommendations, 1):
            response += (
                f"**{i}. Track ID:** `{rec['track_id']}`\n"
                f"   📊 Сходство между вашими привычками и найденным треком: {rec['score'] * 100:.1f}%\n"
                f"   📏 Дистанция: {rec['payload'].get('distance', '?')} км\n"
                f"   ⛰ Рельеф: {rec['payload'].get('terrain', '?')}\n"
                f"   🛣 Маршрут: {rec['payload'].get('route', '?')}\n\n"
            )

        await update.message.reply_text(response, parse_mode="Markdown")


def main():
    init_db()
    init_qdrant()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("recommend", handle_recommend))
    app.add_handler(MessageHandler(filters.COMMAND, start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()


if __name__ == "__main__":
    main()
