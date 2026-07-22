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

# Modèles autorisés + défaut PAR USAGE (maîtrise des coûts).
# - facture (lecture IA) : Sonnet / Haiku uniquement, défaut Haiku (pas d'Opus).
# - copilot : Opus / Sonnet / Haiku, défaut Sonnet (Opus = coûteux, sur demande).
USAGES = {
    "facture": {
        "ids": ["claude-sonnet-5", "claude-haiku-4-5"],
        "defaut": "claude-haiku-4-5",
    },
    "copilot": {
        "ids": ["claude-opus-4-8", "claude-sonnet-5", "claude-haiku-4-5"],
        "defaut": "claude-sonnet-5",
    },
}


def liste(usage: str | None = None) -> dict:
    """Modèles proposés + défaut pour un usage donné (tout si usage inconnu)."""
    cfg = USAGES.get(usage or "")
    if cfg is None:
        return {"modeles": MODELES, "defaut": settings.copilot_model}
    modeles = [_PAR_ID[i] for i in cfg["ids"] if i in _PAR_ID]
    return {"modeles": modeles, "defaut": cfg["defaut"]}


def resoudre(modele: str | None, usage: str | None = None) -> str:
    """Renvoie un id de modèle valide. Si `usage` est fourni, on impose la
    restriction (repli sur le défaut de l'usage si le modèle n'est pas autorisé)."""
    cfg = USAGES.get(usage or "")
    if cfg is not None:
        return modele if modele in cfg["ids"] else cfg["defaut"]
    return modele if modele in _PAR_ID else settings.copilot_model


def kwargs_reflexion(modele: str) -> dict:
    """Paramètres d'appel dépendant du modèle (réflexion adaptative + effort
    pour les modèles qui le supportent, rien sinon)."""
    m = _PAR_ID.get(modele)
    if m and m.get("reflexion"):
        return {"thinking": {"type": "adaptive"}, "output_config": {"effort": "medium"}}
    return {}
