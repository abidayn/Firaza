"""P4.11 - Evaluate the RAG part.

(a) Retrieval Recall@3: hand-written questions whose correct document is known.
(b) Faithfulness: over 20 varied requests, the share of LLM explanations whose numbers
    all appear in the context (verifier passes) - and how often the app fell back.

Run from the repo root:  .venv/Scripts/python ml/eval_rag.py      (uses the Gemini API; ~3 minutes)
Writes ml/reports/rag_eval.json and ml/reports/rag_eval.md
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import models, services  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.rag import explain as ex  # noqa: E402
from app.rag.embeddings import embed_query  # noqa: E402
from app.rag.kb import ensure_kb  # noqa: E402
from app.rag.retrieval import retrieve  # noqa: E402
from app.rag.vector_store import get_store  # noqa: E402

REPORTS = ROOT / "ml" / "reports"

POLICY_QUERIES = [
    ("Pesanan harus sampai besok, vendor mana yang aman?", "policy-urgent_orders"),
    ("Beli 2000 kardus sekaligus, bagaimana memilih harga grosir?", "policy-bulk_orders"),
    ("Benang bordir untuk sajadah custom harus bagus, pilih vendor yang mana?", "policy-quality_sensitive_items"),
    ("Vendor ini sering telat kirim, apakah masih boleh dipakai?", "policy-reliability_threshold"),
    ("Ada supplier baru yang belum pernah kita pakai", "policy-new_vendor_trial"),
    ("Kalau vendor utama kehabisan stok, apa rencana cadangannya?", "policy-backup_vendor"),
]


def vendor_queries(db) -> list[tuple[str, str]]:
    vendors = services.list_rows(db, models.Vendor)[:6]
    out = []
    for i, v in enumerate(vendors):
        if i % 2 == 0:
            out.append((f"Seberapa sering {v.name} terlambat mengirim dan berapa tingkat cacatnya?", f"performance-{v.id}"))
        else:
            out.append((f"Material apa saja yang dijual {v.name} dan berapa harganya?", f"profile-{v.id}"))
    return out


def recall_at_3(db) -> dict:
    store = get_store()
    rows = []
    for q, target in POLICY_QUERIES + vendor_queries(db):
        top = [d["id"] for d in store.query(embed_query(q), n=3)]
        rows.append({"query": q, "target": target, "top3": top, "hit": target in top})
    return {"recall@3": round(float(np.mean([r["hit"] for r in rows])), 3), "n": len(rows), "rows": rows}


def faithfulness(db, n=20, seed=7) -> dict:
    rng = np.random.default_rng(seed)
    mats = [m.id for m in services.list_rows(db, models.Material)]
    rows = []
    for i in range(n):
        w = rng.dirichlet([1, 1, 1])
        rec = services.recommend(db, int(rng.choice(mats)), int(rng.choice([20, 50, 100, 300, 800])),
                                 int(rng.choice([1, 2, 3, 5, 7])), *map(float, w))
        docs = retrieve(rec)
        context = ex.build_context(rec, docs)
        try:
            text, model = ex.generate(f"KONTEKS:\n{context}\n\nTUGAS: jelaskan rekomendasi di atas.", ex.SYSTEM)
            ok = ex.verify_numbers(text, context)
            names_top = rec["results"][0]["vendor_name"] in text
            rows.append({"request_id": rec["request_id"], "status": "llm", "verified": ok,
                         "mentions_top_vendor": names_top, "model": model, "text": text})
        except ex.LLMUnavailable as e:
            rows.append({"request_id": rec["request_id"], "status": "llm_unavailable", "error": str(e)[:200]})
        print(f"  {i + 1}/{n} {rows[-1]['status']} verified={rows[-1].get('verified')}")
        time.sleep(4)   # stay under free-tier requests-per-minute
    answered = [r for r in rows if r["status"] == "llm"]
    return {
        "n_requests": n, "n_answered": len(answered),
        "faithfulness": round(float(np.mean([r["verified"] for r in answered])), 3) if answered else None,
        "mentions_top_vendor": round(float(np.mean([r["mentions_top_vendor"] for r in answered])), 3) if answered else None,
        "rows": rows,
    }


def main() -> None:
    with SessionLocal() as db:
        services.init_db()
        services.seed_if_empty(db)
        ensure_kb(db)
        print("retrieval...")
        r = recall_at_3(db)
        print(f"recall@3 = {r['recall@3']} on {r['n']} queries")
        print("faithfulness (calls Gemini)...")
        f = faithfulness(db)
        print(f"faithfulness = {f['faithfulness']} over {f['n_answered']}/{f['n_requests']} answered")
    result = {"vector_store": get_store().backend_name, "retrieval": r, "generation": f}
    (REPORTS / "rag_eval.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    miss = [x for x in r["rows"] if not x["hit"]]
    lines = ["# RAG evaluation", "",
             "| Metric | Value |", "|---|---|",
             f"| Retrieval Recall@3 ({r['n']} hand-written queries) | {r['recall@3']} |",
             f"| Faithfulness: explanations whose numbers all appear in the context | {f['faithfulness']} "
             f"({f['n_answered']}/{f['n_requests']} requests answered by the LLM) |",
             f"| Explanations that name the rank-1 vendor | {f['mentions_top_vendor']} |",
             "", "Faithfulness is checked automatically: every number in the generated text must appear in the "
             "context given to the model (small list markers excepted). Failing texts are replaced by the template "
             "explanation in the app, so users never see an unverified number.",
             "", f"Vector store used for this run: `{get_store().backend_name}`."]
    if miss:
        lines += ["", "Retrieval misses:"] + [f"- \"{x['query']}\" expected `{x['target']}`, got {x['top3']}" for x in miss]
    (REPORTS / "rag_eval.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
