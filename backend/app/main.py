"""Point d'entrée FastAPI — Boucherie de l'Abbatiale, outil de gestion.

Expose les CRUD référentiels (compatibles Refine) + les imports de
ventes. Étape 1 du cahier des charges.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models, schemas
from .config import settings
from .crud import make_crud_router
from .db import engine
from .routers import achats, copilot, imports, ventes

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

# --- Imports caisse & ventes ---
app.include_router(imports.router)
app.include_router(ventes.router)

# --- Achats (factures fournisseurs) ---
app.include_router(achats.router)

# --- Copilote IA ---
app.include_router(copilot.router)
