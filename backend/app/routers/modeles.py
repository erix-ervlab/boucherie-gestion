"""Liste des modèles IA sélectionnables (selon l'usage)."""

from fastapi import APIRouter

from ..modeles import liste

router = APIRouter(tags=["modeles"])


@router.get("/modeles")
def modeles(usage: str | None = None):
    """Modèles proposés + défaut. `usage` = 'facture' ou 'copilot'."""
    return liste(usage)
