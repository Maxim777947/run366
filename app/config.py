from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ai-sport-bot"
    # PostgreSQL: postgresql+psycopg://USER:PASS@HOST:PORT/DB
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/ai_sport_db"
    )
    # Qdrant: локально или cloud-URL + ключ
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "ai_memory"
    EMBEDDING_DIM: int = 1536  # подбирай под свою модель эмбеддингов

    TELEGRAM_TOKEN: str | None = None  # ← ДОБАВИЛИ

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
