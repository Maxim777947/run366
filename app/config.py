from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ai-sport-bot"
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/ai_sport_db"
    )
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "ai_memory"
    EMBEDDING_DIM: int = 1536

    TELEGRAM_TOKEN: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
