"""Liste des modèles IA sélectionnables."""

from fastapi import APIRouter

from ..config import settings
from ..modeles import MODELES

router = APIRouter(tags=["modeles"])


@router.get("/modeles")
def modeles():
    return {"modeles": MODELES, "defaut": settings.copilot_model}
