"""Retrieval step of RAG: pick the documents the LLM is allowed to use."""
from app.rag.embeddings import embed_query
from app.rag.vector_store import get_store

TOP_VENDORS = 3
TOP_POLICIES = 2


def query_text(rec: dict) -> str:
    w = rec["weights"]
    focus = max(w, key=w.get)
    focus_id = {"price": "harga murah", "speed": "pengiriman cepat dan tepat waktu", "quality": "kualitas tinggi"}[focus]
    urgency = "mendesak" if rec["deadline_days"] <= 2 else "tidak mendesak"
    size = "partai besar" if rec["qty"] >= 300 else "jumlah biasa"
    return (f"Pesanan {rec['qty']} {rec['material_name']} ({size}), tenggat {rec['deadline_days']} hari ({urgency}), "
            f"prioritas utama {focus_id}.")


def retrieve(rec: dict) -> list[dict]:
    """Profile + performance docs of the top vendors (metadata filter) and the most similar policy notes."""
    store = get_store()
    docs = []
    for r in rec["results"][:TOP_VENDORS]:
        docs += sorted(store.get({"vendor_id": r["vendor_id"]}), key=lambda d: d["id"])
    docs += store.query(embed_query(query_text(rec)), n=TOP_POLICIES, where={"type": "policy"})
    return docs
