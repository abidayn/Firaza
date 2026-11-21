"""Business logic shared by the REST API (FastAPI) and the Streamlit app.

Both entry points call these functions, so behavior is identical whichever one is used.
"""
import json
from datetime import date

import pandas as pd
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.core.features import clean_transactions
from app.core.ranker import get_ranker
from app.db import Base, engine


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


class Invalid(Exception):
    pass


# ---------------------------------------------------------------- setup

def init_db() -> None:
    Base.metadata.create_all(engine)


def seed_if_empty(db: Session, reset: bool = False) -> dict:
    """Load the synthetic CSVs (ml/data) into the database if it has no vendors yet."""
    if reset:
        for m in (models.Explanation, models.Recommendation, models.ProcurementRequest, models.Transaction,
                  models.VendorMaterial, models.Material, models.Vendor):
            db.query(m).delete()
        db.commit()
    if db.scalar(select(func.count()).select_from(models.Vendor)):
        return {"seeded": False}
    d = settings.seed_dir
    counts = {}
    for table, model in (("vendors", models.Vendor), ("materials", models.Material),
                         ("vendor_materials", models.VendorMaterial), ("transactions", models.Transaction)):
        df = pd.read_csv(d / f"{table}.csv")
        if table == "transactions":
            df["ordered_at"] = pd.to_datetime(df["ordered_at"]).dt.date
            df["defect_rate"] = df["defect_rate"].astype(object).where(df["defect_rate"].notna(), None)
        db.bulk_insert_mappings(model, df.to_dict(orient="records"))
        db.commit()
        counts[table] = len(df)
    _sync_sequences(db)
    return {"seeded": True, **counts}


def _sync_sequences(db: Session) -> None:
    """After inserting explicit ids into Postgres, move each id sequence past the max id."""
    if engine.dialect.name != "postgresql":
        return
    for t in ("vendors", "materials", "vendor_materials", "transactions"):
        db.execute(text(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), COALESCE(MAX(id), 1)) FROM {t}"))
    db.commit()


# ---------------------------------------------------------------- generic CRUD

def list_rows(db: Session, model, **filters):
    q = select(model)
    for k, v in filters.items():
        if v is not None:
            q = q.where(getattr(model, k) == v)
    return db.scalars(q.order_by(model.id)).all()


def get_row(db: Session, model, row_id: int):
    row = db.get(model, row_id)
    if row is None:
        raise NotFound(f"{model.__tablename__} id {row_id} tidak ditemukan")
    return row


def _check_refs(db: Session, data: dict) -> None:
    for key, model in (("vendor_id", models.Vendor), ("material_id", models.Material)):
        if key in data and db.get(model, data[key]) is None:
            raise Invalid(f"{key} {data[key]} tidak ditemukan")


def create_row(db: Session, model, data: dict):
    _check_refs(db, data)
    row = model(**data)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict("Data duplikat (nama atau pasangan vendor-material sudah ada)")
    db.refresh(row)
    return row


def update_row(db: Session, model, row_id: int, data: dict):
    row = get_row(db, model, row_id)
    _check_refs(db, data)
    for k, v in data.items():
        setattr(row, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict("Perubahan bentrok dengan data yang sudah ada")
    db.refresh(row)
    return row


def delete_row(db: Session, model, row_id: int) -> None:
    row = get_row(db, model, row_id)
    children = {models.Vendor: [models.VendorMaterial, models.Transaction],
                models.Material: [models.VendorMaterial, models.Transaction]}.get(model, [])
    key = "vendor_id" if model is models.Vendor else "material_id"
    for child in children:
        n = db.scalar(select(func.count()).select_from(child).where(getattr(child, key) == row_id))
        if n:
            raise Conflict(f"Tidak bisa dihapus: masih dipakai oleh {n} baris di {child.__tablename__}")
    db.delete(row)
    db.commit()


# ---------------------------------------------------------------- recommendation

def _frames(db: Session, material_id: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    vm = pd.read_sql(select(models.VendorMaterial).where(models.VendorMaterial.material_id == material_id),
                     db.connection())
    tx = pd.read_sql(select(models.Transaction).where(models.Transaction.material_id == material_id),
                     db.connection())
    return vm, clean_transactions(tx)


def normalize_weights(w_price: float, w_speed: float, w_quality: float) -> dict:
    total = w_price + w_speed + w_quality
    if total <= 0:
        raise Invalid("Minimal satu prioritas (harga, kecepatan, kualitas) harus lebih dari 0")
    return {"w_price": w_price / total, "w_speed": w_speed / total, "w_quality": w_quality / total}


def recommend(db: Session, material_id: int, qty: int, deadline_days: int,
              w_price: float, w_speed: float, w_quality: float) -> dict:
    material = db.get(models.Material, material_id)
    if material is None:
        raise NotFound(f"Material id {material_id} tidak ditemukan")
    weights = normalize_weights(w_price, w_speed, w_quality)
    vm, tx = _frames(db, material_id)
    if len(vm) < 2:
        raise Invalid("Material ini punya kurang dari 2 vendor, jadi tidak ada yang bisa dibandingkan")

    req = {"material_id": material_id, "qty": qty, "deadline_days": deadline_days, **weights}
    results = get_ranker().rank(req, vm, tx)
    names = dict(db.execute(select(models.Vendor.id, models.Vendor.name)).all())
    for r in results:
        r["vendor_name"] = names.get(r["vendor_id"], f"Vendor {r['vendor_id']}")

    pr = models.ProcurementRequest(material_id=material_id, qty=qty, deadline_days=deadline_days, **weights)
    db.add(pr)
    db.flush()
    db.add_all(models.Recommendation(request_id=pr.id, vendor_id=r["vendor_id"], rank=r["rank"], score=r["score"],
                                     result_json=json.dumps(r)) for r in results)
    db.commit()
    return _payload(pr, material, results)


def get_recommendation(db: Session, request_id: int) -> dict:
    pr = db.get(models.ProcurementRequest, request_id)
    if pr is None:
        raise NotFound(f"Request id {request_id} tidak ditemukan")
    recs = db.scalars(select(models.Recommendation).where(models.Recommendation.request_id == request_id)
                      .order_by(models.Recommendation.rank)).all()
    return _payload(pr, db.get(models.Material, pr.material_id), [json.loads(r.result_json) for r in recs])


def _payload(pr: models.ProcurementRequest, material: models.Material, results: list[dict]) -> dict:
    return {"request_id": pr.id, "material_id": material.id, "material_name": material.name, "qty": pr.qty,
            "deadline_days": pr.deadline_days,
            "weights": {"price": round(pr.w_price, 3), "speed": round(pr.w_speed, 3),
                        "quality": round(pr.w_quality, 3)},
            "results": results}


def recent_requests(db: Session, limit: int = 10) -> list[dict]:
    rows = db.execute(select(models.ProcurementRequest, models.Material.name)
                      .join(models.Material, models.Material.id == models.ProcurementRequest.material_id)
                      .order_by(models.ProcurementRequest.id.desc()).limit(limit)).all()
    return [{"request_id": pr.id, "material": name, "qty": pr.qty, "deadline_days": pr.deadline_days,
             "created_at": pr.created_at} for pr, name in rows]


def counts(db: Session) -> dict:
    return {m.__tablename__: db.scalar(select(func.count()).select_from(m))
            for m in (models.Vendor, models.Material, models.VendorMaterial, models.Transaction,
                      models.ProcurementRequest)}


def today() -> date:
    return date.today()
