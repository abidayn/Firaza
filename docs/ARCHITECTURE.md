# Architecture

```
                     ┌─────────────────────────────────────────────┐
  Browser ──────────▶│ Streamlit UI  (frontend/Beranda.py + pages) │──┐
                     └─────────────────────────────────────────────┘  │ same Python functions
                     ┌─────────────────────────────────────────────┐  │
  Other apps ───────▶│ FastAPI REST API (backend/app/main.py)      │──┤
  (/api/v1, /docs)   └─────────────────────────────────────────────┘  │
                                                                      ▼
                     ┌───────────────── backend/app/services.py ───────────────────┐
                     │ CRUD · recommend() · explain()                              │
                     └──────┬──────────────────┬──────────────────────┬────────────┘
                            │                  │                      │
              ┌─────────────▼──────┐  ┌────────▼─────────┐  ┌─────────▼──────────────────────┐
              │ Database           │  │ Ranking model    │  │ RAG                            │
              │ SQLite (local)     │  │ core/features.py │  │ kb.py: docs from DB + policies │
              │ Neon Postgres      │  │ core/ranker.py   │  │ embeddings.py: Gemini embed    │
              │ (production)       │  │ LightGBM file    │  │ vector_store.py: ChromaDB      │
              └────────────────────┘  └──────────────────┘  │ retrieval.py → llm.py (Gemini) │
                                                            │ explain.py: verify + fallback  │
                                                            └────────────────────────────────┘
  Offline (not deployed): ml/  generate data → build ranking dataset → train → evaluate
```

## Why this shape
- **Individual Generative AI track:** the playbook allows a monolith or a decoupled design and requires at least a Streamlit inference UI. The UI calls the service layer directly (one deploy, fewer moving parts). The FastAPI app exposes the *same* functions as an inference API with interactive docs, because the Firaza use case asks for recommendations to be available through an inference API.
- **One feature module** (`core/features.py`) is imported by both the training scripts and the app, so features are always computed the same way.
- **The model decides the ranking; the LLM only explains it.** The LLM gets the ranking, the model's per-feature contributions, and retrieved documents, and must use only numbers from that context (checked by `verify_numbers`).
- **Graceful degradation:** if Gemini is down, rate-limited, or its text fails the number check, a deterministic template explanation is shown. The app never crashes because of the AI part.
- **API keys** only live in environment variables / platform secrets and are only used server-side.

## Request flow: "Cari rekomendasi"
1. UI collects material, quantity, deadline, priorities → `services.recommend()`.
2. Load that material's offers and transactions from the DB → `clean_transactions()` → `build_candidate_features()`.
3. LightGBM scores each vendor and returns per-feature contributions; results are sorted and saved (`procurement_requests`, `recommendations`).
4. UI shows the table and charts, then calls `explain()`:
   - make sure the knowledge base is indexed (embeddings cached on disk),
   - retrieve the top-3 vendors' profile and performance docs (metadata filter) plus the 2 most similar policy notes (semantic search),
   - build the context, call Gemini (models tried in order), verify numbers, save to `explanations`.

## Database tables
`vendors`, `materials`, `vendor_materials` (offer: price, bulk price, MOQ, lead time, stock, quality), `transactions`, `procurement_requests`, `recommendations` (rank, score, full result JSON with contributions), `explanations` (text, source, model, retrieved doc ids).

## Vector store note
In deployment (Linux) the vector store is ChromaDB. On the Windows development machine, the OS's Application Control policy blocks a native DLL that chromadb loads, so the app automatically falls back to an in-memory NumPy cosine index with the same interface. `/api/v1/health` and the home page show which one is active.
