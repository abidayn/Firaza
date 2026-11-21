"""CRUD endpoints for vendors, materials, vendor offers, and transactions."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models, schemas, services
from app.db import get_db


def crud_router(prefix: str, model, schema_in, schema_out, tag: str, filters: tuple[str, ...] = ()) -> APIRouter:
    r = APIRouter(prefix=prefix, tags=[tag])

    if filters:
        @r.get("", response_model=list[schema_out], summary=f"List {tag.lower()}")
        def list_items(db: Session = Depends(get_db),
                       vendor_id: int | None = Query(None), material_id: int | None = Query(None)):
            f = {k: v for k, v in {"vendor_id": vendor_id, "material_id": material_id}.items() if k in filters}
            return services.list_rows(db, model, **f)
    else:
        @r.get("", response_model=list[schema_out], summary=f"List {tag.lower()}")
        def list_items(db: Session = Depends(get_db)):
            return services.list_rows(db, model)

    @r.get("/{item_id}", response_model=schema_out, summary=f"Get one {tag.lower()} row")
    def get_item(item_id: int, db: Session = Depends(get_db)):
        return services.get_row(db, model, item_id)

    @r.post("", response_model=schema_out, status_code=201, summary=f"Create {tag.lower()} row")
    def create_item(body: schema_in, db: Session = Depends(get_db)):
        return services.create_row(db, model, body.model_dump())

    @r.put("/{item_id}", response_model=schema_out, summary=f"Update {tag.lower()} row")
    def update_item(item_id: int, body: schema_in, db: Session = Depends(get_db)):
        return services.update_row(db, model, item_id, body.model_dump())

    @r.delete("/{item_id}", status_code=204, summary=f"Delete {tag.lower()} row")
    def delete_item(item_id: int, db: Session = Depends(get_db)):
        services.delete_row(db, model, item_id)

    return r


vendors = crud_router("/vendors", models.Vendor, schemas.VendorIn, schemas.VendorOut, "Vendors")
materials = crud_router("/materials", models.Material, schemas.MaterialIn, schemas.MaterialOut, "Materials")
vendor_materials = crud_router("/vendor-materials", models.VendorMaterial, schemas.VendorMaterialIn,
                               schemas.VendorMaterialOut, "Vendor offers", filters=("vendor_id", "material_id"))
transactions = crud_router("/transactions", models.Transaction, schemas.TransactionIn, schemas.TransactionOut,
                           "Transactions", filters=("vendor_id", "material_id"))
