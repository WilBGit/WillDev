from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Client
from backend.services.ai import generate_caption_async

router = APIRouter(prefix="/ai", tags=["ai"])

class PrefsIn(BaseModel):
    client_id: int
    categories: list[str] = []
    ai_auto: bool = True
    model: str | None = None
    timezone: str | None = None
    post_time_hour: int | None = None
    post_time_minute: int | None = None

@router.post("/prefs")
def set_prefs(body: PrefsIn, db: Session = Depends(get_db)):
    c = db.query(Client).filter(Client.id==body.client_id).first()
    if not c: return {"error":"client not found"}
    c.preferences_json = {"categories": body.categories, "ai_auto": body.ai_auto}
    if body.model: c.model_name = body.model
    if body.timezone: c.timezone = body.timezone
    if body.post_time_hour is not None: c.post_time_hour = body.post_time_hour
    if body.post_time_minute is not None: c.post_time_minute = body.post_time_minute
    db.add(c); db.commit()
    return {"ok": True}

class GenerateIn(BaseModel):
    client_id: int
    brief: str | None = None  # if None and ai_auto=True, we still generate

@router.post("/generate-once")
async def generate_once(body: GenerateIn, db: Session = Depends(get_db)):
    c = db.query(Client).filter(Client.id==body.client_id).first()
    if not c: return {"error":"client not found"}
    cats = (c.preferences_json or {}).get("categories", [])
    result = await generate_caption_async(body.brief or "", cats, c.city, c.model_name)
    return {"ok": True, "result": result}