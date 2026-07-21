"""Endpoint du copilote IA (Claude + outil SQL lecture seule)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import settings

router = APIRouter(prefix="/copilot", tags=["copilot"])


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    modele: str | None = None


@router.get("/status")
def status():
    return {"configure": bool(settings.anthropic_api_key), "modele": settings.copilot_model}


@router.post("/chat")
def chat(req: ChatRequest):
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="Copilote non configuré : la clé ANTHROPIC_API_KEY est absente.",
        )
    # Import différé : évite de charger le SDK/engine si le copilote n'est pas utilisé.
    from .. import copilot as copilot_mod

    try:
        return copilot_mod.chat([m.model_dump() for m in req.messages], req.modele)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Erreur copilote : {e}")
