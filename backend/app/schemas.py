"""Schémas Pydantic (I/O API) pour les référentiels CRUD.

Read / Create / Update par ressource. Les Read sont configurés en
`from_attributes` pour sérialiser directement les objets SQLAlchemy.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class _Read(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Famille ---
class FamilleBase(BaseModel):
    code: str | None = None
    nom: str


class FamilleCreate(FamilleBase):
    pass


class FamilleUpdate(BaseModel):
    code: str | None = None
    nom: str | None = None


class FamilleRead(_Read, FamilleBase):
    id: int


# --- Sous-famille ---
class SousFamilleBase(BaseModel):
    famille_id: int
    code: str | None = None
    nom: str


class SousFamilleCreate(SousFamilleBase):
    pass


class SousFamilleUpdate(BaseModel):
    famille_id: int | None = None
    code: str | None = None
    nom: str | None = None


class SousFamilleRead(_Read, SousFamilleBase):
    id: int


# --- Fournisseur ---
class FournisseurBase(BaseModel):
    nom: str
    actif: bool = True


class FournisseurCreate(FournisseurBase):
    pass


class FournisseurUpdate(BaseModel):
    nom: str | None = None
    actif: bool | None = None


class FournisseurRead(_Read, FournisseurBase):
    id: int


# --- Produit (PLU) ---
class ProduitBase(BaseModel):
    code_plu: str
    nom: str
    famille_id: int | None = None
    sous_famille_id: int | None = None
    tva: Decimal = Decimal("5.50")
    prix_vente: Decimal | None = None
    actif: bool = True


class ProduitCreate(ProduitBase):
    pass


class ProduitUpdate(BaseModel):
    code_plu: str | None = None
    nom: str | None = None
    famille_id: int | None = None
    sous_famille_id: int | None = None
    tva: Decimal | None = None
    prix_vente: Decimal | None = None
    actif: bool | None = None


class ProduitRead(_Read, ProduitBase):
    id: int


# --- Journal d'import (lecture seule côté API) ---
class ImportJournalRead(_Read):
    id: int
    fichier_nom: str
    nb_lignes_ajoutees: int
    nb_lignes_deja_connues: int
    nb_lignes_ignorees: int
    nb_anomalies: int
    anomalies: str | None = None
    z_min: int | None = None
    z_max: int | None = None
