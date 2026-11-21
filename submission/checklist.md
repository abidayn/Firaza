# Submission checklist (requirement → evidence)

✅ done · ⏳ waiting on you · ➖ optional

## Learning path Generative AI, individual (Main Quest)
| Requirement | Evidence | Status |
|---|---|---|
| AI model built to fit the data (own training, no TF Hub / AutoML) | `ml/train_ranker.py`, `backend/artifacts/ranker.txt`, `docs/MODEL_CARD.md` | ✅ |
| Preprocessing before the model | `backend/app/core/features.py`, `ml/reports/eda_cleaning_before_after.png` | ✅ |
| Citations for datasets, libraries, models | `README.md` (References), `docs/SBOM.md`, `docs/DATA_CARD.md` | ✅ |
| Generative feature via proprietary API (waived by RAG) | Gemini generation in `backend/app/rag/llm.py` | ✅ |
| Inference UI (Streamlit minimum) | `frontend/Beranda.py` + `frontend/pages/` | ✅ |
| Not "LLM API as first feature" | first feature = trained ranker; LLM explains it | ✅ |

## Side Quest: RAG
| Requirement | Evidence | Status |
|---|---|---|
| Generation model (Gemini API) | `backend/app/rag/llm.py` | ✅ |
| Embedding model (Gemini embedding API) | `backend/app/rag/embeddings.py` | ✅ |
| Vector database (ChromaDB) | `backend/app/rag/vector_store.py` | ✅ |
| Integrated into the app | Recommend page → "Penjelasan AI" | ✅ |
| Evaluated | `ml/reports/rag_eval.md` (Recall@3 1.0, faithfulness 1.0) | ✅ |

## General capstone rules
| Requirement | Evidence | Status |
|---|---|---|
| Web tech, dynamic output from user input | Streamlit app | ✅ |
| Live URL (not localhost) | Streamlit Cloud (see `docs/DEPLOY.md`) | ⏳ deploy |
| Data persisted in a real database | Neon Postgres via `DATABASE_URL` | ⏳ paste Neon string |
| AI feature contextual, integrated server-side (key safe) | `backend/app/rag/`, keys in env/secrets; repo scanned clean | ✅ |
| Errors handled without crashing | global API error handler, UI messages, template fallback; 14 tests | ✅ |
| REST API with interactive docs (use case: inference API) | FastAPI `/docs` (local) | ✅ (➖ public deploy on Render) |
| Open source MIT, permissive deps, SBOM | `LICENSE`, `docs/SBOM.md`, `docs/LICENSE_NOTES.md` | ✅ (3 indirect MPL deps documented) |
| No personal/confidential data | synthetic data only | ✅ |
| Repo proves own work | github.com/abidayn/Firaza, commits authored by abidayn | ✅ |

## Firaza use case indicators
| Indicator | Evidence | Status |
|---|---|---|
| Admin manages vendors and procurement info via web | Vendor, Material & Harga, Transaksi pages | ✅ |
| Stores price, lead time, quality, history | DB tables `vendor_materials`, `transactions` | ✅ |
| User inputs a procurement need | Recommend page form | ✅ |
| AI model ranks vendors | LightGBM LambdaRank | ✅ |
| Results available via inference API | `POST /api/v1/recommendations` | ✅ |
| GenAI explains reasons and trade-offs | RAG explanation | ✅ |
| End-to-end need → recommendation → comparison | tested in browser and with `AppTest` | ✅ |
| Ranking method evaluated and documented | `ml/reports/metrics.md`, `docs/MODEL_CARD.md` | ✅ |

## Final deliverables
| Item | File / link | Status |
|---|---|---|
| Project Brief (official template) | draft content: `submission/brief/project_brief_draft.md` | ⏳ template + links + screenshots |
| Usage guide or demo video | `docs/USER_GUIDE.md`; script `submission/videos/demo_script.md` | ⏳ record demo |
| Slides (6-part outline) | `submission/slides/firaza_pitch.pptx` | ✅ (add 1 screenshot on slide 9) |
| 10-minute presentation video, face on camera, Indonesian | script `submission/videos/presentation_script.md` | ⏳ record + upload |
| Submit the form before 22 Nov 23:59 WIB | — | ⏳ |
| 360 feedback (20–24 Nov) | — | ⏳ |
