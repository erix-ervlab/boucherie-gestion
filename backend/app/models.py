"""Schéma de données — Étape 1 du cahier des charges.

Référentiels (famille, sous_famille, produit/PLU, fournisseur) + ventes
importées depuis l'export GDPdU de la caisse + journal des imports.

Les tables achats / correspondance fournisseur / rendements viendront
aux étapes 3 et 6 (cf. docs/cahier-des-charges-gestion-boucherie.md §6).
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Famille(Base):
    """Grande catégorie correspondant à ce qu'on achète (Bœuf, Porc, Veau…)."""

    __tablename__ = "famille"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str | None] = mapped_column(String(32), unique=True)
    nom: Mapped[str] = mapped_column(String(120), unique=True)

    sous_familles: Mapped[list["SousFamille"]] = relationship(
        back_populates="famille", cascade="all, delete-orphan"
    )


class SousFamille(Base):
    """Découpe plus fine d'une famille (ex. Bœuf « à griller » / « à mijoter »)."""

    __tablename__ = "sous_famille"
    __table_args__ = (
        UniqueConstraint("famille_id", "nom", name="uq_sousfamille_famille_nom"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    famille_id: Mapped[int] = mapped_column(
        ForeignKey("famille.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str | None] = mapped_column(String(32))
    nom: Mapped[str] = mapped_column(String(120))

    famille: Mapped[Famille] = relationship(back_populates="sous_familles")


class Fournisseur(Base):
    __tablename__ = "fournisseur"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(160), unique=True)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class Produit(Base):
    """PLU — l'article précis vendu en caisse (code + prix propres).

    Catalogue importé au démarrage depuis l'Excel existant (291 PLU),
    puis géré exclusivement via CRUD.
    """

    __tablename__ = "produit"

    id: Mapped[int] = mapped_column(primary_key=True)
    code_plu: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    nom: Mapped[str] = mapped_column(String(200))
    famille_id: Mapped[int | None] = mapped_column(ForeignKey("famille.id"))
    sous_famille_id: Mapped[int | None] = mapped_column(ForeignKey("sous_famille.id"))
    tva: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), default=Decimal("5.50"), server_default="5.50"
    )
    prix_vente: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))  # €/kg ou €/pièce
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class ImportJournal(Base):
    """Historique des dépôts d'export caisse (cf. cahier §3.1)."""

    __tablename__ = "import_journal"

    id: Mapped[int] = mapped_column(primary_key=True)
    fichier_nom: Mapped[str] = mapped_column(String(255))
    periode_debut: Mapped[date | None] = mapped_column(Date)
    periode_fin: Mapped[date | None] = mapped_column(Date)
    date_depot: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    nb_lignes_ajoutees: Mapped[int] = mapped_column(Integer, default=0)
    nb_lignes_deja_connues: Mapped[int] = mapped_column(Integer, default=0)
    nb_lignes_ignorees: Mapped[int] = mapped_column(Integer, default=0)  # types 2/3/4, annulations, copies
    nb_anomalies: Mapped[int] = mapped_column(Integer, default=0)
    anomalies: Mapped[str | None] = mapped_column(Text)  # JSON : trous de Z, etc.
    z_min: Mapped[int | None] = mapped_column(Integer)
    z_max: Mapped[int | None] = mapped_column(Integer)


class VenteLigne(Base):
    """Une ligne de vente (Type_enregistrement=1) issue de l'export GDPdU.

    Import idempotent : la contrainte d'unicité sur la clé métier permet
    un upsert (ON CONFLICT DO NOTHING) — réimporter un export chevauchant
    ne duplique rien.
    """

    __tablename__ = "vente_ligne"
    __table_args__ = (
        UniqueConstraint(
            "id_sd_device",
            "numero_rapport_z",
            "numero_ticket",
            "type_enregistrement",
            "n_plu",
            "poids_gramme",
            "montant",
            "position_ticket",
            name="uq_vente_ligne_cle_metier",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # --- clé métier de déduplication (cf. cahier §3.1) ---
    id_sd_device: Mapped[str] = mapped_column(String(64), index=True)
    numero_rapport_z: Mapped[int] = mapped_column(Integer, index=True)
    numero_ticket: Mapped[int] = mapped_column(Integer)
    type_enregistrement: Mapped[int] = mapped_column(Integer)  # =1 après nettoyage
    n_plu: Mapped[str] = mapped_column(String(32), index=True)
    poids_gramme: Mapped[int] = mapped_column(Integer)  # 0 si vendu à la pièce
    montant: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # distingue deux lignes strictement identiques dans un même ticket
    # (cf. ticket 3173 : « Chorizo ibérique » deux fois, poids différents)
    position_ticket: Mapped[int] = mapped_column(Integer, default=0)

    # --- attributs ---
    date_vente: Mapped[date | None] = mapped_column(Date, index=True)
    horodatage: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    produit_id: Mapped[int | None] = mapped_column(ForeignKey("produit.id"))
    # Conservé pour audit fiscal, mais JAMAIS compté dans le CA/kg.
    annule: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    import_id: Mapped[int | None] = mapped_column(ForeignKey("import_journal.id"))
