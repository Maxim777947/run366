from uuid import uuid4
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel, Field
from qdrant_client import models
from app.infrastructure.db.qdrant import client
from app.config import settings

router = APIRouter(prefix="/memory", tags=["memory"])


from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.infrastructure.db.postgres import get_session
from app.domian.models.users import User


router = APIRouter(prefix="/users", tags=["users"])




@router.post("", response_model=User)
def create_user(payload: User, session: Session = Depends(get_session)):
    exists = session.exec(select(User).where(User.tg_id == payload.tg_id)).first()
    if exists:
        raise HTTPException(status_code=409, detail="tg_id already exists")
    session.add(payload)
    session.commit()
    session.refresh(payload)
    return payload

@router.get("/{tg_id}", response_model=User)
def get_user(tg_id: int, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.tg_id == tg_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="not found")
    return user




class IngestReq(BaseModel):
    user_id: str
    text: str
    dense: list[float] = Field(min_length=1)

class SearchReq(BaseModel):
    user_id: str
    dense: list[float]
    k: int = 5

@router.post("/ingest")
def ingest(req: IngestReq):
    client.upsert(
        collection_name=settings.QDRANT_COLLECTION,
        points=[models.PointStruct(
            id=str(uuid4()),
            vector={"dense": req.dense},
            payload={
                "user_id": req.user_id,
                "text": req.text,
                "ts": datetime.utcnow().isoformat()
            }
        )]
    )
    return {"ok": True}

@router.post("/search")
def search(req: SearchReq):
    hits = client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=("dense", req.dense),
        query_filter=models.Filter(must=[
            models.FieldCondition(key="user_id", match=models.MatchValue(req.user_id))
        ]),
        limit=req.k,
        with_payload=True
    )
    return [{"score": h.score, "text": h.payload.get("text"), "id": h.id} for h in hits]



