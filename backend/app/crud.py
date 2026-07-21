"""Fabrique de routers CRUD génériques compatibles Refine (simple-rest).

Le data-provider `@refinedev/simple-rest` attend :
- liste paginée via `_start` / `_end`, triée via `_sort` / `_order`,
- le total renvoyé dans l'en-tête `X-Total-Count`,
- filtres d'égalité passés en query-string (`champ=valeur`).

`make_crud_router` évite de réécrire ces cinq endpoints par ressource.
"""

from typing import Type

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from .db import get_db

_RESERVED = {"_start", "_end", "_sort", "_order"}


def make_crud_router(
    *,
    resource: str,
    model: Type,
    read_schema: Type,
    create_schema: Type,
    update_schema: Type,
    default_sort: str = "id",
) -> APIRouter:
    router = APIRouter(prefix=f"/{resource}", tags=[resource])

    @router.get("", response_model=list[read_schema])
    def list_(
        response: Response,
        request: Request,
        db: Session = Depends(get_db),
        _start: int = 0,
        _end: int = 25,
        _sort: str = default_sort,
        _order: str = "ASC",
    ):
        query = db.query(model)

        # Filtres d'égalité sur les colonnes existantes du modèle.
        for key, value in request.query_params.items():
            if key in _RESERVED:
                continue
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)

        total = query.count()

        sort_col = getattr(model, _sort, None) or getattr(model, "id")
        query = query.order_by(
            sort_col.desc() if _order.upper() == "DESC" else sort_col.asc()
        )

        items = query.offset(_start).limit(max(_end - _start, 0)).all()

        response.headers["X-Total-Count"] = str(total)
        response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
        return items

    @router.get("/{item_id}", response_model=read_schema)
    def get_one(item_id: int, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(404, f"{resource} {item_id} introuvable")
        return obj

    @router.post("", response_model=read_schema, status_code=201)
    def create(payload: create_schema, db: Session = Depends(get_db)):  # type: ignore[valid-type]
        obj = model(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @router.patch("/{item_id}", response_model=read_schema)
    def update(item_id: int, payload: update_schema, db: Session = Depends(get_db)):  # type: ignore[valid-type]
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(404, f"{resource} {item_id} introuvable")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        db.commit()
        db.refresh(obj)
        return obj

    # Refine émet un PUT pour l'édition standard : on l'aligne sur le PATCH.
    router.add_api_route(
        "/{item_id}", update, methods=["PUT"], response_model=read_schema
    )

    @router.delete("/{item_id}", response_model=read_schema)
    def delete(item_id: int, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(404, f"{resource} {item_id} introuvable")
        db.delete(obj)
        db.commit()
        return obj

    return router
