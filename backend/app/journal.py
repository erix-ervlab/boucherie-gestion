"""Journal d'audit — helper d'enregistrement des opérations.

L'entrée est ajoutée à la session courante (pas de commit ici) : elle est
donc persistée avec la transaction de l'appelant — atomique (si l'opération
échoue et est annulée, l'entrée de journal l'est aussi).
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from .models import JournalOperation


def enregistrer(
    db: Session,
    action: str,
    entite: str,
    libelle: str,
    entite_id: int | None = None,
    details: dict | None = None,
) -> None:
    db.add(
        JournalOperation(
            action=action,
            entite=entite,
            entite_id=entite_id,
            libelle=libelle,
            details=json.dumps(details, ensure_ascii=False) if details else None,
        )
    )
