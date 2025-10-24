from fastapi import FastAPI
from app.config import settings
from app.infrastructure.db.postgres import init_db
from app.infrastructure.db.qdrant import init_qdrant
from app.adapters.api.routers import users

app = FastAPI(title=settings.APP_NAME)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(users.router)


# инициализация БД на старте
@app.on_event("startup")
def on_startup():
    init_db()
    init_qdrant()
