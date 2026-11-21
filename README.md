# Firaza · Vendor Recommendation & Procurement Assistant

Capstone project, **Dicoding Bootcamp Batch 15**: individual, Generative AI learning path (ID DB15-I036, Abid Dayyan).
Use case: **Firaza** (retail hampers and personalized gifts), *Use Case 3: Vendor Recommendation & Procurement Assistant*.

A decision-support web app that helps Firaza's owner choose suppliers for packaging and production materials.
You enter a need (material, quantity, deadline, priorities) and:

1. a **learning-to-rank model trained from scratch** (LightGBM LambdaRank) orders the candidate vendors using price, lead time, quality, on-time history, defect rate, MOQ, and stock;
2. a **RAG pipeline** (Gemini embeddings → vector store → Gemini) explains *why*, using retrieved vendor profiles, performance summaries, and procurement notes, in Indonesian, grounded in the model's own feature contributions.

The final decision stays with the owner or staff. **All data is synthetic** (Firaza did not provide data).

- **Live app:** https://firaza-vendor.streamlit.app (Streamlit Community Cloud, ChromaDB vector store, Neon Postgres)
- **Learning pre-read:** [`docs/PRE_READ.md`](docs/PRE_READ.md) · **Plan:** [`plan.md`](plan.md)

## Results

| | Metric | Value |
|---|---|---|
| Ranking model (test set, 450 unseen requests) | NDCG@3 | **0.933** (target ≥ 0.85) |
| Best simple baseline (weighted sum of user priorities) | NDCG@3 | 0.788 |
| Shuffled-label control | NDCG@3 | 0.456 (chance level) |
| RAG retrieval (12 hand-written queries) | Recall@3 | **1.0** |
| RAG generation (20 varied requests) | faithfulness: every number traceable to the context | **1.0** on 18 answered (2 hit Gemini overload → template fallback) |

Details: [`ml/reports/metrics.md`](ml/reports/metrics.md) · [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md) · [`docs/DATA_CARD.md`](docs/DATA_CARD.md)

## Architecture

```
Streamlit UI (frontend/) ─┐
                          ├─▶ backend/app/services.py ─▶ DB (SQLite local / Neon Postgres)
FastAPI REST API ─────────┘                          ├─▶ LightGBM ranker (backend/artifacts/ranker.txt)
 (/api/v1, Swagger /docs)                            └─▶ RAG: Gemini embeddings → ChromaDB → Gemini
ml/  (offline): generate synthetic data → build ranking dataset → train → evaluate
```
More in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Run locally

Requirements: Python 3.12 and a Gemini API key (free, from Google AI Studio).

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt      # Windows path; on macOS/Linux use .venv/bin/python
cp .env.example .env                                              # then fill in GEMINI_API_KEY
```

| Task | Command |
|---|---|
| Web app (Streamlit) | `.venv/Scripts/python -m streamlit run frontend/Beranda.py` |
| REST API + Swagger at http://localhost:8000/docs | `.venv/Scripts/python -m uvicorn app.main:app --app-dir backend --port 8000` |
| Seed / reset the database | `.venv/Scripts/python backend/scripts/seed.py [--reset] [--target prod]` |
| Check the Gemini key and model ids | `.venv/Scripts/python backend/scripts/check_gemini.py` |
| Tests (14) | `cd backend && ../.venv/Scripts/python -m pytest -q` |
| Regenerate data and retrain | `python ml/generate_data.py && python ml/build_ranking_dataset.py && python ml/train_ranker.py && python ml/evaluate.py` |
| EDA charts / RAG evaluation | `python ml/eda.py` · `python ml/eval_rag.py` |

The app creates and seeds its database on first start if it is empty.

### Environment variables (names only; values go in `.env` or platform secrets)
`GEMINI_API_KEY`, `GEMINI_GEN_MODEL` (comma-separated list, tried in order), `GEMINI_EMBED_MODEL`, `DATABASE_URL`, `PROD_DATABASE_URL`.

## REST API (inference)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/health` | model loaded, vector store in use |
| GET/POST/PUT/DELETE | `/api/v1/vendors`, `/materials`, `/vendor-materials`, `/transactions` | CRUD |
| POST | `/api/v1/recommendations` | rank vendors for `{material_id, qty, deadline_days, w_price, w_speed, w_quality}` |
| GET | `/api/v1/recommendations/{id}` | saved result |
| POST | `/api/v1/recommendations/{id}/explanation` | RAG explanation (`source`: `llm` / `fallback` / `fallback_unverified`) |
| POST/GET | `/api/v1/kb/rebuild`, `/api/v1/kb/status` | knowledge-base index |

## Repository layout
```
backend/   app/ (FastAPI, services, models, core/features+ranker, rag/), artifacts/ (trained model), kb/ (policy notes, embedding cache), scripts/, tests/
frontend/  Streamlit app: Beranda.py + pages/
ml/        data generation, ranking dataset, baselines, training, evaluation, EDA, RAG eval; data/ and reports/
docs/      PRE_READ, DATA_CARD, MODEL_CARD, ARCHITECTURE, USER_GUIDE, DEPLOY, SBOM, LICENSE_NOTES
```

## Limitations
- Synthetic data: labels come from a simulated utility function, so metrics show the pipeline works, not accuracy on Firaza's real decisions.
- No user login (prototype). Free hosting tiers sleep when idle and the Gemini free tier is rate-limited; the app then shows a template explanation instead of failing.
- Knowledge-base policy notes are illustrative assumptions, not Firaza's official policy.

## References
- Burges, C. J. C. (2010). *From RankNet to LambdaRank to LambdaMART: An Overview*. Microsoft Research MSR-TR-2010-82.
- Ke, G. et al. (2017). *LightGBM: A Highly Efficient Gradient Boosting Decision Tree*. NeurIPS.
- Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS.
- Järvelin, K., & Kekäläinen, J. (2002). *Cumulated Gain-Based Evaluation of IR Techniques*. ACM TOIS (NDCG).
- Hwang, C. L., & Yoon, K. (1981). *Multiple Attribute Decision Making*. Springer (TOPSIS baseline).
- Google Gemini API (embeddings `gemini-embedding-2`, generation `gemini-3.5-flash-lite` / `gemini-3.8-flash`).
- Dicoding Bootcamp Batch 15, *Use Case UMKM — Firaza*.
- Libraries and licenses: [`docs/SBOM.md`](docs/SBOM.md), notes in [`docs/LICENSE_NOTES.md`](docs/LICENSE_NOTES.md).

## License
MIT. See [`LICENSE`](LICENSE).
