"""Knowledge base for RAG: documents built from the database + policy notes."""
import threading
from datetime import date, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.core.features import clean_transactions
from app.rag.embeddings import embed_documents
from app.rag.vector_store import get_store

_lock = threading.Lock()


def _rp(x: float) -> str:
    return "Rp " + f"{x:,.0f}".replace(",", ".")


def build_documents(db: Session) -> list[dict]:
    vendors = pd.read_sql(select(models.Vendor), db.connection())
    mats = pd.read_sql(select(models.Material), db.connection()).set_index("id")
    vm = pd.read_sql(select(models.VendorMaterial), db.connection())
    tx = clean_transactions(pd.read_sql(select(models.Transaction), db.connection()))
    if not tx.empty:
        tx["ordered_at"] = pd.to_datetime(tx["ordered_at"])
    six_months_ago = pd.Timestamp(date.today() - timedelta(days=182))

    docs = []
    for v in vendors.itertuples():
        offers = vm[vm.vendor_id == v.id]
        lines = [f"- {mats.at[o.material_id, 'name']}: {_rp(o.unit_price)} per {mats.at[o.material_id, 'unit']}, "
                 f"lead time {o.lead_time_days} hari, MOQ {o.moq}, kualitas {o.quality_score:.1f}/5"
                 + ("" if o.in_stock else ", stok kosong") for o in offers.itertuples()]
        docs.append({"id": f"profile-{v.id}", "meta": {"type": "profile", "vendor_id": int(v.id)},
                     "text": f"Profil vendor {v.name} ({v.city}). {v.notes}. Material yang dijual:\n" + "\n".join(lines)})

        h = tx[tx.vendor_id == v.id]
        if h.empty:
            perf = f"Kinerja vendor {v.name}: belum ada histori transaksi."
        else:
            ontime = (h.actual_days <= h.promised_days).mean() * 100
            late = h[h.actual_days > h.promised_days]
            avg_delay = (late.actual_days - late.promised_days).mean() if len(late) else 0.0
            recent = (h.ordered_at >= six_months_ago).sum()
            perf = (f"Kinerja vendor {v.name}: {len(h)} transaksi tercatat, {recent} di antaranya dalam 6 bulan "
                    f"terakhir. Tepat waktu {ontime:.0f}% dari pesanan. Saat terlambat, rata-rata terlambat "
                    f"{avg_delay:.1f} hari. Rata-rata tingkat cacat {h.defect_rate.mean() * 100:.1f}%.")
        docs.append({"id": f"performance-{v.id}", "meta": {"type": "performance", "vendor_id": int(v.id)},
                     "text": perf})

    for path in sorted((settings.kb_dir / "policies").glob("*.md")):
        docs.append({"id": f"policy-{path.stem}", "meta": {"type": "policy", "vendor_id": -1},
                     "text": path.read_text(encoding="utf-8").strip()})
    return docs


def rebuild_kb(db: Session) -> int:
    with _lock:
        docs = build_documents(db)
        vectors = embed_documents([d["text"] for d in docs])
        store = get_store()
        store.reset()
        store.add([d["id"] for d in docs], vectors, [d["text"] for d in docs], [d["meta"] for d in docs])
        return store.count()


def ensure_kb(db: Session) -> int:
    store = get_store()
    if store.count() == 0:
        return rebuild_kb(db)
    return store.count()
