"""HTTP Adapter (FastAPI).

Responsibilities:
- Expose HTTP API and translate HTTP requests/responses to application layer.
- Initialize infrastructure at process startup (DB, clients), wire dependencies.

Constraints:
- Must not contain domain logic or direct SQL/ORM usage (beyond init).
- Depends on application use cases and domain ports; inject infrastructure implementations.
"""

from fastapi import FastAPI
from app.config import settings
from app.infrastructure.db.postgres import init_db
# Optional: Qdrant init can be added when the module exists
# from app.infrastructure.db.qdrant import init_qdrant
# from app.adapters.api.routers import users

app = FastAPI(title=settings.APP_NAME)


# @app.get("/health")
# def health():
#     return {"status": "ok"}


# app.include_router(users.router)


# инициализация БД на старте
@app.on_event("startup")
def on_startup():
    init_db()
    # init_qdrant()  # enable when qdrant integration is available
