"""Point d'entrée FastAPI — Boucherie de l'Abbatiale, outil de gestion.

Expose les CRUD référentiels (compatibles Refine) + les imports de
ventes. Étape 1 du cahier des charges.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from . import models, schemas
from .config import settings
from .crud import make_crud_router
from .db import engine
from .routers import (
    achats,
    copilot,
    gammes,
    imports,
    journal,
    marge,
    modeles,
    rendement,
    ventes,
)

app = FastAPI(title="Boucherie de l'Abbatiale — Gestion", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)


@app.on_event("startup")
def _startup() -> None:
    # Dev uniquement : crée les tables. En prod, basculer sur Alembic.
    if settings.dev_create_all:
        models.Base.metadata.create_all(bind=engine)
        # create_all n'ajoute pas les colonnes manquantes sur une table déjà
        # créée : on ajoute gamme_id après coup, de façon idempotente.
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE correspondance_fournisseur "
                    "ADD COLUMN IF NOT EXISTS gamme_id integer "
                    "REFERENCES gamme_decoupe(id) ON DELETE SET NULL"
                )
            )


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# --- Référentiels CRUD (Étape 1) ---
app.include_router(
    make_crud_router(
        resource="familles",
        model=models.Famille,
        read_schema=schemas.FamilleRead,
        create_schema=schemas.FamilleCreate,
        update_schema=schemas.FamilleUpdate,
    )
)
app.include_router(
    make_crud_router(
        resource="sous-familles",
        model=models.SousFamille,
        read_schema=schemas.SousFamilleRead,
        create_schema=schemas.SousFamilleCreate,
        update_schema=schemas.SousFamilleUpdate,
    )
)
app.include_router(
    make_crud_router(
        resource="fournisseurs",
        model=models.Fournisseur,
        read_schema=schemas.FournisseurRead,
        create_schema=schemas.FournisseurCreate,
        update_schema=schemas.FournisseurUpdate,
    )
)
app.include_router(
    make_crud_router(
        resource="produits",
        model=models.Produit,
        read_schema=schemas.ProduitRead,
        create_schema=schemas.ProduitCreate,
        update_schema=schemas.ProduitUpdate,
        default_sort="code_plu",
    )
)
app.include_router(
    make_crud_router(
        resource="correspondances",
        model=models.CorrespondanceFournisseur,
        read_schema=schemas.CorrespondanceRead,
        create_schema=schemas.CorrespondanceCreate,
        update_schema=schemas.CorrespondanceUpdate,
        default_sort="reference_fournisseur",
    )
)

# --- Imports caisse & ventes ---
app.include_router(imports.router)
app.include_router(ventes.router)

# --- Achats (factures fournisseurs) ---
app.include_router(achats.router)

# --- Marge par famille ---
app.include_router(marge.router)

# --- Gammes de découpe + rendement (Étape 6) ---
app.include_router(gammes.router)
app.include_router(rendement.router)

# --- Journal d'audit ---
app.include_router(journal.router)

# --- Copilote IA ---
app.include_router(copilot.router)

# --- Modèles IA sélectionnables ---
app.include_router(modeles.router)
