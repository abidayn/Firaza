"""Explain a ranking in Indonesian, grounded in retrieved documents and the model's own reasons.

The ranking model decides the order. The LLM only puts that decision into words,
using numbers we give it. If the LLM is unavailable, or its text contains numbers
that are not in the context, a deterministic template explanation is used instead.
"""
import json
import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.rag.embeddings import EmbeddingUnavailable
from app.rag.kb import ensure_kb
from app.rag.llm import LLMUnavailable, generate
from app.rag.retrieval import retrieve

log = logging.getLogger("firaza.explain")

SYSTEM = (
    "Kamu asisten procurement untuk UMKM Firaza. Jelaskan MENGAPA urutan vendor ini direkomendasikan. "
    "Urutan sudah diputuskan oleh model ranking; jangan mengubahnya. "
    "Gunakan hanya angka dan fakta dalam KONTEKS, salin angkanya persis seperti tertulis. "
    "Jangan menghitung angka baru dan jangan menyebut vendor yang tidak ada di KONTEKS. "
    "Jika informasi tidak tersedia, tulis 'tidak tersedia'. Bahasa Indonesia, maksimal 120 kata, tanpa markdown. "
    "Struktur: (1) rekomendasi utama dan alasannya, (2) trade-off dibanding alternatif, (3) satu risiko atau catatan."
)

FEATURE_WORDS = {
    "unit_price_eff": "harga satuan", "price_rel_median": "harga dibanding vendor lain", "lead_typ": "lama pengiriman",
    "slack_typ": "sisa waktu terhadap tenggat", "lead_p90": "lama pengiriman terburuk (histori)",
    "slack_p90": "sisa waktu terhadap tenggat (histori terburuk)", "quality_score": "skor kualitas",
    "ontime_rate": "ketepatan waktu", "defect_rate": "tingkat cacat", "moq_ratio": "minimum order (MOQ)",
    "in_stock": "ketersediaan stok", "n_tx": "jumlah histori transaksi", "deadline_days": "tenggat",
    "log_qty": "jumlah pesanan", "w_price": "prioritas harga", "w_speed": "prioritas kecepatan",
    "w_quality": "prioritas kualitas",
}


def rp(x: float) -> str:
    return "Rp " + f"{x:,.0f}".replace(",", ".")


def pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def top_reasons(r: dict, n: int = 3) -> list[str]:
    """Strongest features pushing this vendor's score, in words (from LightGBM pred_contrib)."""
    items = sorted(r["contributions"].items(), key=lambda kv: abs(kv[1]), reverse=True)
    items = [kv for kv in items if not kv[0].startswith("w_")][:n]
    return [f"{FEATURE_WORDS.get(k, k)} ({'menaikkan' if v > 0 else 'menurunkan'} skor)" for k, v in items]


def facts(rec: dict) -> dict:
    res = rec["results"]
    top = res[0]
    cheapest = min(res, key=lambda r: r["total_price"])
    runner = res[1] if len(res) > 1 else None
    out = {
        "top": top, "cheapest": cheapest, "runner": runner,
        "late": [r for r in res if r["misses_deadline"]],
        "diff_vs_cheapest": top["total_price"] - cheapest["total_price"],
        "diff_vs_cheapest_pct": (top["total_price"] - cheapest["total_price"]) / cheapest["total_price"]
        if cheapest["total_price"] else 0,
    }
    if runner:
        out["diff_vs_runner"] = top["total_price"] - runner["total_price"]
    return out


def build_context(rec: dict, docs: list[dict]) -> str:
    f = facts(rec)
    w = rec["weights"]
    lines = [f"PERMINTAAN: {rec['qty']} {rec['material_name']}, tenggat {rec['deadline_days']} hari. "
             f"Bobot prioritas: harga {pct(w['price'])}, kecepatan {pct(w['speed'])}, kualitas {pct(w['quality'])}.",
             "", "HASIL RANKING MODEL (urutan final):"]
    for r in rec["results"][:5]:
        flags = []
        if r["misses_deadline"]:
            flags.append(f"melewati tenggat ({r['lead_time_days']} hari > {rec['deadline_days']} hari)")
        if r["below_moq"]:
            flags.append("pesanan di bawah MOQ vendor")
        if not r["in_stock"]:
            flags.append("stok kosong")
        lines.append(f"#{r['rank']} {r['vendor_name']}: harga satuan {rp(r['unit_price'])}, total {rp(r['total_price'])}, "
                     f"lead time {r['lead_time_days']} hari, kualitas {r['quality_score']:.1f}/5, "
                     f"tepat waktu {pct(r['ontime_rate'])}, cacat {r['defect_rate'] * 100:.1f}%"
                     + (f"; {', '.join(flags)}" if flags else ""))
    lines += ["", f"FAKTOR TERKUAT UNTUK #{f['top']['rank']} {f['top']['vendor_name']} (dari model): "
              + "; ".join(top_reasons(f["top"]))]
    if f["cheapest"]["vendor_id"] != f["top"]["vendor_id"]:
        lines.append(f"SELISIH: {f['top']['vendor_name']} lebih mahal {rp(f['diff_vs_cheapest'])} "
                     f"({pct(f['diff_vs_cheapest_pct'])}) dibanding vendor termurah {f['cheapest']['vendor_name']}.")
    else:
        lines.append(f"SELISIH: {f['top']['vendor_name']} sekaligus vendor termurah.")
    lines += ["", "DOKUMEN PENDUKUNG:"] + [f"[{d['id']}] {d['text']}" for d in docs]
    return "\n".join(lines)


def fallback_explanation(rec: dict) -> str:
    f = facts(rec)
    top = f["top"]
    s = (f"{top['vendor_name']} direkomendasikan di peringkat 1 untuk {rec['qty']} {rec['material_name']}. "
         f"Faktor terkuat menurut model: {', '.join(top_reasons(top))}. "
         f"Harga satuan {rp(top['unit_price'])} (total {rp(top['total_price'])}), lead time {top['lead_time_days']} hari, "
         f"tepat waktu {pct(top['ontime_rate'])}, kualitas {top['quality_score']:.1f}/5. ")
    if f["cheapest"]["vendor_id"] != top["vendor_id"]:
        s += (f"Vendor ini {rp(f['diff_vs_cheapest'])} ({pct(f['diff_vs_cheapest_pct'])}) lebih mahal dari "
              f"{f['cheapest']['vendor_name']} yang termurah"
              + (", namun vendor termurah itu melewati tenggat. " if f["cheapest"]["misses_deadline"] else ". "))
    else:
        s += "Vendor ini sekaligus yang termurah. "
    late = [r["vendor_name"] for r in f["late"] if r["vendor_id"] != top["vendor_id"]]
    if late:
        s += f"Vendor yang diperkirakan melewati tenggat {rec['deadline_days']} hari: {', '.join(late[:4])}."
    if top["misses_deadline"]:
        s += " Catatan: rekomendasi utama pun diperkirakan melewati tenggat; pertimbangkan memperpanjang tenggat."
    return s.strip()


_NUM = re.compile(r"\d+(?:[.,]\d+)*")


def _norm(tok: str) -> str:
    return tok.replace(".", "").replace(",", "")


def verify_numbers(text: str, context: str) -> bool:
    """Every number in the LLM text must appear in the context (small integers like list markers are allowed)."""
    allowed = {_norm(t) for t in _NUM.findall(context)}
    for tok in _NUM.findall(text):
        n = _norm(tok)
        if n.isdigit() and int(n) <= 10:
            continue
        if n not in allowed:
            return False
    return True


def explain(db: Session, rec: dict) -> dict:
    """Return the cached explanation or create one (LLM with fallback)."""
    request_id = rec["request_id"]
    cached = db.scalar(select(models.Explanation).where(models.Explanation.request_id == request_id))
    if cached:
        return _out(cached)

    source, model, sources = "fallback", "", []
    text = fallback_explanation(rec)
    try:
        ensure_kb(db)
        docs = retrieve(rec)
        sources = [d["id"] for d in docs]
        context = build_context(rec, docs)
        llm_text, model = generate(f"KONTEKS:\n{context}\n\nTUGAS: jelaskan rekomendasi di atas.", SYSTEM)
        if verify_numbers(llm_text, context):
            text, source = llm_text, "llm"
        else:
            source = "fallback_unverified"
    except (LLMUnavailable, EmbeddingUnavailable) as exc:
        log.warning("explanation falls back to template: %s", exc)
        source = "fallback"
    except Exception:  # never let the explanation break the app
        log.exception("unexpected error in RAG path; using template explanation")
        source = "fallback"

    row = models.Explanation(request_id=request_id, text=text, source=source, model=model,
                             sources_json=json.dumps(sources))
    db.add(row)
    db.commit()
    return _out(row)


def _out(row: models.Explanation) -> dict:
    return {"request_id": row.request_id, "text": row.text, "source": row.source, "model": row.model,
            "sources": json.loads(row.sources_json or "[]")}
