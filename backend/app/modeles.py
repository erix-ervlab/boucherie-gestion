"""Modèles Claude sélectionnables + adaptation des paramètres d'appel.

Le modèle peut être choisi par requête (copilote, lecture de factures)
pour maîtriser le coût. On valide le modèle demandé contre cette liste
(sinon on retombe sur le modèle par défaut), et on adapte les paramètres
selon les capacités du modèle : Opus 4.8 / Sonnet 5 supportent la
réflexion adaptative + `effort` ; Haiku 4.5 non (il faut les omettre,
sinon l'API renvoie une erreur).
"""

from .config import settings

MODELES = [
    {
        "id": "claude-opus-4-8",
        "nom": "Opus 4.8",
        "cout": "le plus fin, coût élevé",
        "reflexion": True,
    },
    {
        "id": "claude-sonnet-5",
        "nom": "Sonnet 5",
        "cout": "bon compromis, coût moyen",
        "reflexion": True,
    },
    {
        "id": "claude-haiku-4-5",
        "nom": "Haiku 4.5",
        "cout": "rapide et économique",
        "reflexion": False,
    },
]

_PAR_ID = {m["id"]: m for m in MODELES}


def resoudre(modele: str | None) -> str:
    """Renvoie un id de modèle valide (repli sur le modèle par défaut)."""
    return modele if modele in _PAR_ID else settings.copilot_model


def kwargs_reflexion(modele: str) -> dict:
    """Paramètres d'appel dépendant du modèle (réflexion adaptative + effort
    pour les modèles qui le supportent, rien sinon)."""
    m = _PAR_ID.get(modele)
    if m and m.get("reflexion"):
        return {"thinking": {"type": "adaptive"}, "output_config": {"effort": "medium"}}
    return {}
