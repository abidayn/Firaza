# plan.md — Firaza Vendor Recommendation & Procurement Assistant

Execution plan from an empty folder to submitted deliverables. Written 2026-11-21 14:30 WIB.
**Hard deadline: Sunday 2026-11-22, 23:59 WIB** (final deliverables form). Internal target: submit by **21:00**.

## How to use this file
- Tasks are atomic checkboxes: `- [ ] **P1.3** (ME) ...`. Each has a **Done when** check that can be verified by a command or by looking.
- **(ME)** = the coding agent does it. **(YOU)** = only you can do it (accounts, keys, clicking, recording).
- To run a phase, say `run P1`. I execute tasks in order, tick the boxes in this file, and stop at the phase **Gate**.
- At each Gate I ask you **2 questions** (one sentence each). That is the learning check; it takes 2 minutes and keeps you able to defend the project.
- Anything that needs your account, key, or an outward action (creating the GitHub repo, pushing, deploying) waits for your explicit "go".
- Never paste API keys or connection strings into chat. They go only into `.env` (git-ignored).

**Status (2026-11-21, 16:30 WIB):** P0–P5 done; P6–P7 done except the steps that need your accounts and the recordings (see "Your remaining steps").

## Progress log and changes made during execution
- **Cross-check (individual GenAI track):** the full-stack checklist (React, Express, module bundler, mandatory decoupling) does **not** apply. Still required: own model + preprocessing + citations + Streamlit inference UI + live URL + persistent DB + server-side AI; RAG is the side quest. The use case still asks for vendor CRUD and an inference API, so both exist. The UI calls the service layer directly (monolith allowed for individuals) and FastAPI exposes the same functions.
- **D1 changed:** repo is `github.com/abidayn/Firaza` (yours). Commits authored by Abid Dayyan (GitHub noreply email), no Claude co-author.
- **D3 detail:** `gemini-embedding-2` merges a list of strings into one vector, so each text is sent as its own `Content`. Embeddings are cached on disk (`backend/kb/embeddings_cache.json`) because the free tier allows ~100 embed requests per minute.
- **D4 detail:** `GEMINI_GEN_MODEL` is a list (`gemini-3.5-flash-lite`, then `gemini-3.8-flash`); the newer flash models were returning 503/504 under load.
- **D5 detail:** Windows Application Control on this PC blocks chromadb's and faiss's native DLLs, so locally the app falls back to an in-memory NumPy index automatically; the Linux deploy uses ChromaDB.
- **D8 changed:** Streamlit is the single deployed app (Streamlit Community Cloud); FastAPI runs locally with Swagger (optional on Render). `frontend/app.py` is now `frontend/Beranda.py`.
- **P5.1 changed:** no HTTP client (the UI calls services directly).
- **Results:** ranker NDCG@3 0.933 (best baseline 0.788, shuffled-label control 0.456); RAG Recall@3 1.0, faithfulness 1.0 (18/20 answered; 2 hit Gemini overload and got the template).

## Your remaining steps (in order)
1. **Neon (P0.8):** Neon console → project `sweet-dream-44689469` → **Connect** → copy the connection string → `.env` `PROD_DATABASE_URL`. Neon's `npm`/`neon deploy` prompt targets JavaScript apps and is not needed here.
2. **Deploy on Streamlit Community Cloud (P6.5)** following `docs/DEPLOY.md`, then send me the URL. I run the live checks (P6.4, P6.6, P6.7), add the URL to the README and brief, and tag the release (P6.10).
3. **Project Brief template (P7.4):** drop it in `submission/brief/`; I fill it from `project_brief_draft.md` (P7.5).
4. **Screenshots (P7.6), demo video (P7.9), 10-minute presentation video (P7.10), submit (P7.12), 360 feedback (P7.13).**
5. After submitting: rotate the Gemini key (it was pasted in chat once).

---

## 0. Decisions (fixed, so we do not re-debate under deadline)

| # | Decision | Why |
|---|---|---|
| D1 | One GitHub repo `abidayn/firaza-vendor-assistant` with `backend/` and `frontend/` as separately deployed apps | Individual track allows decoupled or monolith; one repo is less overhead. (Project Plan said two repos; note the change in the Project Brief.) |
| D2 | Database: SQLite locally, Neon Postgres in production, same SQLAlchemy code, driver `pg8000` | Persistent live DB without the LGPL driver `psycopg2` |
| D3 | Embeddings via **Gemini embedding API**, not local multilingual-e5 | `torch` would blow the free-host memory limit. Course allows "embedding via API service". (Project Plan said e5; note the change in the Project Brief.) |
| D4 | Generation via Gemini API (free tier). Model ids are read from `.env`, found by `check_gemini.py` | Avoids guessing model names |
| D5 | Vector DB: ChromaDB, rebuilt from the database at startup / on demand | Free hosts have ephemeral disks. Contingency if Render runs out of memory: swap to FAISS (P6.9) |
| D6 | No Docker. Render builds Python natively | Fewer moving parts |
| D7 | No login (cut). Documented as a prototype limitation | Time |
| D8 | UI: Streamlit calling the REST API only | Course minimum for the individual Gen AI path |
| D9 | All data synthetic; hidden ground truth kept out of the DB and the API | Keeps the ML honest (see P1.1) |

## 1. Folder structure (already created)

```
FINALPROJECT/
├─ plan.md  README.md  LICENSE  .gitignore  .env.example  requirements-dev.txt
├─ docs/            PRE_READ.md (exists) + DATA_CARD.md MODEL_CARD.md USER_GUIDE.md SBOM.md LICENSE_NOTES.md ARCHITECTURE.md
├─ deliverables/    Project Plan (.odt/.pdf, exists)
├─ submission/      brief/  slides/  videos/  (final deliverables work area)
├─ ml/              OFFLINE work (not deployed)
│  ├─ requirements.txt
│  ├─ data/         generated CSVs   (data/_latent/ = hidden truth, git-ignored)
│  ├─ reports/      metrics.json, EDA images
│  └─ generate_data.py  build_ranking_dataset.py  eda.py  baselines.py  train_ranker.py  evaluate.py  eval_rag.py
├─ backend/         FastAPI app (deployed to Render)
│  ├─ requirements.txt
│  ├─ artifacts/    ranker.txt  feature_names.json
│  ├─ kb/policies/  *.md  (RAG policy documents)
│  ├─ app/          main.py config.py db.py models.py schemas.py
│  │   ├─ routers/  health.py vendors.py materials.py vendor_materials.py transactions.py recommendations.py kb.py
│  │   ├─ core/     features.py ranker.py
│  │   └─ rag/      embeddings.py kb.py retrieval.py llm.py explain.py
│  ├─ scripts/      check_gemini.py seed.py
│  └─ tests/
└─ frontend/        Streamlit app (deployed to Streamlit Community Cloud)
   ├─ requirements.txt  app.py  api_client.py
   ├─ pages/        1_Vendors.py 2_Materials_Prices.py 3_Transactions.py 4_Recommend.py
   └─ .streamlit/   secrets.toml.example
```

## 2. Timeline and cut rules

| Phase | Window (WIB) | Output |
|---|---|---|
| P0 Setup | Sat 14:30–16:00 | Python, key, DB, repo, venv working |
| P1 Data + preprocessing | Sat 16:00–18:30 | Synthetic data, features, EDA |
| P2 Ranking model | Sat 18:30–21:00 | Trained ranker + evaluation vs baselines |
| break | Sat 21:00–22:00 | |
| P3 Backend | Sat 22:00–00:30 | API with DB, CRUD, `/recommendations` |
| sleep | | |
| P4 RAG | Sun 08:00–10:30 | Explanation endpoint with fallback |
| P5 Frontend | Sun 10:30–12:30 | Streamlit pages |
| P6 Deploy | Sun 12:30–15:00 | **Code freeze 15:00**, live URL |
| P7 Docs + videos + submit | Sun 15:00–21:00 | Submitted |

**Cut rules (apply automatically if a Gate is missed by more than 30 min):**
1. P2: stop tuning. Report whatever NDCG you have. Do not chase 0.85.
2. P3: drop Materials CRUD and Transactions write endpoints. Seed them by script. Keep Vendors + VendorMaterials CRUD and `/recommendations`.
3. P4: drop the numeric verifier (P4.9) and the 15-scenario eval. Keep retrieval + generation + fallback.
4. P5: drop pages 2 and 3. Keep Vendors and Recommend.
5. P7: slides stay plain. No extra polish.
**Never cut:** trained ranker with evaluation, `/recommendations`, RAG explanation with fallback, persistent DB, live URL, SBOM/licenses, both videos.

---

# P0 — Setup and accounts (Sat 14:30–16:00)

- [x] **P0.1** (YOU) Install Python 3.12. In PowerShell: `winget install -e --id Python.Python.3.12` (or download from python.org and tick "Add python.exe to PATH"). Then **close and reopen the terminal / Claude Code session**.
  **Done when:** `python --version` prints `Python 3.12.x`. *(Python is not installed today; nothing else can start without it.)*
- [x] **P0.2** (ME) Create the virtual environment at the repo root: `python -m venv .venv`.
  **Done when:** `.\.venv\Scripts\python --version` prints 3.12.x.
- [x] **P0.3** (ME) `.\.venv\Scripts\python -m pip install -U pip` then `.\.venv\Scripts\python -m pip install -r requirements-dev.txt`.
  **Done when:** `.\.venv\Scripts\python -c "import fastapi, sqlalchemy, pg8000, pandas, lightgbm, chromadb, streamlit, faker, matplotlib; from google import genai; print('imports ok')"` prints `imports ok`.
  If `chromadb` fails to install: note the error, continue, and use the FAISS contingency in P4.4 (`pip install faiss-cpu`).
- [x] **P0.4** (ME) Pin exact versions: write `pip freeze` entries for the packages named in `backend/requirements.txt`, `ml/requirements.txt`, `frontend/requirements.txt` back into those files as `name==version`.
  **Done when:** every line in the three files contains `==`.
- [x] **P0.5** (YOU) Gemini API key: open https://aistudio.google.com/apikey, sign in, **Create API key** (free tier). Copy `.env.example` to `.env` and paste the key after `GEMINI_API_KEY=`. Do **not** put it in chat or git.
  **Done when:** `.env` exists and `GEMINI_API_KEY=` has a value (I check only that the length is greater than 0; I never print it).
- [x] **P0.6** (ME) Write `backend/scripts/check_gemini.py`: load `.env`; list models whose supported actions include `generateContent` and `embedContent`; print only model names; make one test generation ("Jawab satu kata: halo") and one embedding call; print the vector length.
  **Done when:** running it prints a model list, a one-word reply, and an embedding length greater than 100.
- [x] **P0.7** (YOU) From the printed list pick one text model with "flash" in the name and one embedding model (name contains "embedding"). Put them in `.env` as `GEMINI_GEN_MODEL=` and `GEMINI_EMBED_MODEL=`. (Or tell me the two names and I write them; they are not secret.)
  **Done when:** re-running `check_gemini.py` with those env values passes.
- [ ] **P0.8** (YOU) Neon database: sign up at https://neon.tech, create a project (name `firaza`, region Singapore), copy the **connection string** (starts with `postgresql://`), paste it in `.env` after `PROD_DATABASE_URL=`.
  **Done when:** `.env` line is non-empty.
- [x] **P0.9** (ME) `git init -b main`. **Done when:** `git status` runs without error. No commit yet.
- [x] **P0.10** (YOU) Say **"go repo"** to authorize creating a **public** GitHub repo (you are logged in as `abidayn`). (ME) then runs `gh repo create abidayn/firaza-vendor-assistant --public --source . --remote origin`, makes the first commit (scaffold only; reference PDFs and `.env` are git-ignored), and pushes.
  **Done when:** https://github.com/abidayn/firaza-vendor-assistant opens and does not contain `.env`, the playbook PDF, or the use case HTML.

**Gate P0:** P0.1–P0.10 ticked. Questions: (1) Why is `.env` in `.gitignore`? (2) Why did we choose the Gemini embedding API over a local embedding model?

---

# P1 — Synthetic data and preprocessing (Sat 16:00–18:30)

Concept to hold: features = what the model sees; label = the "right answer"; hidden truth = what only the simulator knows.

- [x] **P1.1** (ME) Write `ml/generate_data.py` (fixed `random.seed(42)` / `numpy default_rng(42)`). It creates, under `ml/data/`:
  - `materials.csv` (12 rows): kardus 30x20x15 cm, kardus 40x30x20 cm, pita satin 2 cm, pita grosgrain, plastik bubble wrap, polymailer, kotak hampers premium, kertas kado, benang bordir, label stiker, tali rafia, lakban. Columns `id,name,category,unit` (categories: packaging, ribbon, embroidery_printing).
  - `vendors.csv` (32 rows): `id,name,city,notes`. Names like "CV Kemasan Jaya", cities from Bandung, Jakarta, Surabaya, Semarang, Tangerang, Bekasi, Solo, Yogyakarta.
  - `vendor_materials.csv`: `id,vendor_id,material_id,unit_price,bulk_min_qty,bulk_unit_price,moq,lead_time_days,in_stock,quality_score`. Each vendor supplies 4–7 materials; **every material has at least 5 vendors**. `quality_score` is a noisy observed rating.
  - `transactions.csv`: `id,vendor_id,material_id,qty,unit_price,ordered_at,promised_days,actual_days,defect_rate`, about 1,800 rows over the last 18 months.
  - `_latent/vendor_truth.csv` (git-ignored): `vendor_id,reliability_true,quality_true` — the hidden truth used **only** to make training labels.
  - Latent rules: `reliability_true ~ Beta(8,2)` clipped to [0.6,0.99]; `quality_true ~ N(3.8,0.5)` clipped to [2.5,5]. A transaction is late with probability `1 - reliability_true` (delay 1–4 days), otherwise `actual_days = promised_days` or one day early. `defect_rate ~` mean `(5-quality_true)/20`. Observed `quality_score = quality_true + N(0,0.25)` clipped to [1,5].
  - Deliberate dirt in `transactions.csv`: about 2% `defect_rate` empty, 1% duplicated rows, 0.5% `actual_days` outliers (40+), so preprocessing has real work.
  **Done when:** `.\.venv\Scripts\python ml\generate_data.py` prints row counts (12 / 32 / ≥150 / ~1,800) and the four CSVs plus `_latent\vendor_truth.csv` exist.
- [x] **P1.2** (ME) Write `backend/app/core/features.py` (this single module is used by training **and** by the API, to avoid training/serving skew):
  - `FEATURE_NAMES` (17): `deadline_days, log_qty, w_price, w_speed, w_quality, unit_price_eff, price_rel_median, lead_typ, slack_typ, lead_p90, slack_p90, quality_score, ontime_rate, defect_rate, moq_ratio, in_stock, n_tx`.
  - `clean_transactions(tx)`: drop duplicate rows; drop rows with `actual_days > 30`; fill missing `defect_rate` with the vendor median, falling back to the global median; enforce dtypes.
  - `build_candidate_features(req, vm, tx)` → DataFrame indexed by `vendor_id`. `req` has `material_id, qty, deadline_days, w_price, w_speed, w_quality`. `unit_price_eff` = `bulk_unit_price` if `qty >= bulk_min_qty` else `unit_price`. `price_rel_median` = price ÷ median price of the candidates. `slack_typ = deadline_days - lead_typ`; `slack_p90 = deadline_days - lead_p90`. `lead_p90` = 90th percentile of `actual_days` for that vendor-material, falling back to `lead_typ*1.3` when there is no history. `ontime_rate = (on_time_count + 0.85*3) / (n_tx + 3)` (prior smoothing). `moq_ratio = moq / qty`. `n_tx` = number of transactions for the pair.
  **Done when:** a smoke call on the CSVs returns a DataFrame with the 17 columns, no NaN, one row per vendor for the chosen material.
- [x] **P1.3** (ME) Write `backend/tests/test_features.py`: (a) `clean_transactions` removes the injected duplicates and outliers, (b) no NaN left in `defect_rate`, (c) bulk price applied only at or above `bulk_min_qty`, (d) column order equals `FEATURE_NAMES`.
  **Done when:** `cd backend; ..\.venv\Scripts\python -m pytest tests/test_features.py -q` shows all passed.
- [x] **P1.4** (ME) Write `ml/build_ranking_dataset.py`: create 3,000 simulated requests (material uniform; `qty` from {20,50,100,200,500}; `deadline_days` from {1,2,3,5,7,10} weighted toward 2–5; weights `(w_price,w_speed,w_quality)` drawn from Dirichlet(1,1,1)). For each request, features come from `build_candidate_features`. The **label** (0–4) comes from this utility, which uses the hidden truth:
  ```
  price_s   = 1 - (p - pmin)/(pmax - pmin)                       # among the request's candidates
  slack_s   = clip((deadline - lead_typ + 3)/6, 0, 1)
  qual_s    = sqrt(clip((quality_true - 1)/4, 0, 1))              # diminishing returns
  speed_s   = 0.6*slack_s + 0.4*reliability_true
  u = w_price*price_s + w_speed*speed_s + w_quality*qual_s
  if deadline <= 2:        u -= 0.25*(1 - reliability_true)       # urgency x reliability interaction
  if lead_typ > deadline:  u -= 0.30                              # hard deadline miss
  if qty < moq:            u -= 0.20
  u += Normal(0, 0.04)                                            # judgement noise
  u_norm = (u - min(u in group)) / (max(u in group) - min(u in group))
  label  = min(4, floor(u_norm * 5))
  ```
  Output `ml/data/ranking_train.csv` with `request_id`, the 17 features, `label`, and a column `split` assigned **per request** (70% train / 15% val / 15% test, seed 42).
  **Done when:** the file exists, every `request_id` has at least 5 rows, labels cover 0–4, and no `request_id` appears in more than one split.
- [x] **P1.5** (ME) Write `ml/eda.py` (matplotlib, saves PNGs to `ml/reports/`): `eda_ontime_by_vendor.png`, `eda_price_vs_lead.png`, `eda_label_distribution.png`, `eda_cleaning_before_after.png` (rows and missing counts before/after cleaning).
  **Done when:** the four PNGs exist and open.
- [x] **P1.6** (ME) Write `docs/DATA_CARD.md`: what is synthetic and why, every table/column, the latent-truth design, the label formula in plain words, the known limitation ("labels derive from a function we wrote; results are prototype-level"), and licenses/citations (data is self-generated; libraries listed in SBOM later).
  **Done when:** the file exists and mentions the limitation sentence.

**Gate P1:** P1.1–P1.6 ticked, `pytest` green. Questions: (1) What is a feature and what is a label in our data? (2) Why do labels use hidden truth instead of the observed columns?

---

# P2 — Ranking model and evaluation (Sat 18:30–21:00)

- [x] **P2.1** (ME) Write `ml/baselines.py` with three functions that each take a request's candidate DataFrame and return a score per vendor: `cheapest` (lower price = higher score), `weighted_sum` (linear: `w_price*price_s + w_speed*(1 - lead_typ/max_lead) + w_quality*(quality_score-1)/4`), `topsis` (criteria: price cost, lead_typ cost, quality benefit, ontime_rate benefit; weights = `w_price,w_speed,w_quality` split so speed weight is shared by lead and ontime).
  **Done when:** each returns one finite score per candidate on a sample request.
- [x] **P2.2** (ME) In `ml/evaluate.py` implement `ndcg_at_k(y_true, y_score, k)` with gain `2^rel - 1` and `log2(position+1)` discount (same as LightGBM default), applied per request and averaged. Add mean Kendall τ per request (`scipy.stats.kendalltau`).
  **Done when:** a quick check on true grades [4,3,1,0] gives NDCG@3 = 1.0 for the perfect order and a clearly lower value (below 0.7) for the reversed order [0,1,3,4].
- [x] **P2.3** (ME) Write `ml/train_ranker.py`: sort rows by `request_id`, compute group sizes, train `lgb.LGBMRanker(objective="lambdarank", n_estimators=500, learning_rate=0.05, num_leaves=15, min_child_samples=20, subsample=0.8, colsample_bytree=0.8, random_state=42)` with `eval_set` on the validation split, `eval_group`, `eval_at=[1,3,5]`, `callbacks=[lgb.early_stopping(30)]`. Save `backend/artifacts/ranker.txt` (`model.booster_.save_model`) and `backend/artifacts/feature_names.json` (the 17 names in order).
  **Done when:** both artifact files exist and the log shows the best iteration and validation NDCG@3.
- [x] **P2.4** (ME) Run `ml/evaluate.py` on the **test** split: NDCG@1/3/5 and Kendall τ for the model, `cheapest`, `weighted_sum`, `topsis`, plus a **control** model trained on shuffled labels. Save `ml/reports/metrics.json` and `ml/reports/metrics.md` (a table).
  **Done when:** `metrics.json` has all five rows × four metrics; the shuffled-label control is clearly lower than the real model.
- [x] **P2.5** (ME) Report the result honestly. If model NDCG@3 ≥ 0.85 and above all baselines: say so. If not: one tuning pass only (max 30 min; learning rate, `num_leaves`), then report as is.
  **Done when:** `ml/reports/metrics.md` contains a plain-language conclusion paragraph.
- [x] **P2.6** (ME) Feature importance + contributions: save `ml/reports/feature_importance.png` and verify `booster.predict(X, pred_contrib=True)` returns shape `(n, 18)` (17 features + bias) and that each row sums to the raw score (tolerance 1e-6).
  **Done when:** the PNG exists and the sum check passes.
- [x] **P2.7** (ME) "Break it" experiment (feeds the learning check): drop `slack_typ` and `slack_p90`, retrain quickly, record the NDCG@3 drop in `metrics.md`.
  **Done when:** the result is written in `metrics.md`.
- [x] **P2.8** (ME) Write `docs/MODEL_CARD.md`: purpose, training data (synthetic), features, algorithm, metrics table, baselines, limitations (circularity, synthetic data), intended use (decision support only), how to retrain.
  **Done when:** the file exists with the metrics table.

**Gate P2:** artifacts + metrics exist. Questions: (1) Why must the train/test split be by request, not by row? (2) What did the shuffled-label control tell us?

---

# P3 — Backend API (Sat 22:00–00:30)

- [x] **P3.1** (ME) `backend/app/config.py` (pydantic-settings; reads `.env` and `../.env`; fields: `database_url` default `sqlite:///./firaza.db`, `gemini_api_key`, `gemini_gen_model`, `gemini_embed_model`, `artifacts_dir`, `kb_dir`).
  **Done when:** `from app.config import settings` works and prints no secret.
- [x] **P3.2** (ME) `backend/app/db.py`: SQLAlchemy engine + `SessionLocal` + `get_db`. If the URL starts with `postgresql://` or `postgres://`, rewrite to `postgresql+pg8000://`, strip the `sslmode` and `channel_binding` query parameters, and pass `connect_args={"ssl_context": True}`. (pg8000 rejects `sslmode`.)
  **Done when:** a unit test shows the rewrite for a sample Neon-style URL.
- [x] **P3.3** (ME) `backend/app/models.py` tables: `Vendor(id,name unique,city,notes)`, `Material(id,name unique,category,unit)`, `VendorMaterial(id,vendor_id FK,material_id FK,unit_price,bulk_min_qty,bulk_unit_price,moq,lead_time_days,in_stock,quality_score; unique(vendor_id,material_id))`, `Transaction(id,vendor_id,material_id,qty,unit_price,ordered_at,promised_days,actual_days,defect_rate)`, `ProcurementRequest(id,material_id,qty,deadline_days,w_price,w_speed,w_quality,created_at)`, `Recommendation(id,request_id,vendor_id,rank,score,contributions_json)`, `Explanation(id,request_id,text,source,created_at)`. `Base.metadata.create_all` at startup.
  **Done when:** starting the app creates `firaza.db` with 7 tables.
- [x] **P3.4** (ME) `backend/app/schemas.py` (Pydantic): create/read models for each table; `RecommendationIn` validates `qty>=1`, `1<=deadline_days<=30`, weights each in [0,1] (normalized server-side so they sum to 1; if all zero → 400 with a clear message).
  **Done when:** invalid payloads in a test return 422.
- [x] **P3.5** (ME) `backend/app/main.py` with `FastAPI(title="Firaza Vendor Recommendation API", version="1.0")`, router prefix `/api/v1`, and a global exception handler returning JSON (no stack traces). `health.py`: `GET /api/v1/health` → `{"status":"ok","model_loaded":bool}`.
  **Done when:** `GET /api/v1/health` returns 200.
- [x] **P3.6** (ME) CRUD routers (list/get/create/update/delete): `vendors.py`, `materials.py`, `vendor_materials.py`; `transactions.py` (list with filters `vendor_id`, `material_id`; create; delete). Deleting a vendor with children returns 409 with a clear message (no silent cascade).
  **Done when:** Swagger at `/docs` shows every route, and a create → read → update → delete round trip works on `vendors`.
- [x] **P3.7** (ME) `backend/scripts/seed.py`: read `ml/data/*.csv` and insert into whatever `DATABASE_URL` points to (`--target prod` uses `PROD_DATABASE_URL`). Idempotent: skips if vendors already exist unless `--reset`.
  **Done when:** `..\.venv\Scripts\python scripts\seed.py` (from `backend/`) prints inserted counts and `GET /api/v1/vendors` returns 32 vendors.
- [x] **P3.8** (ME) `backend/app/core/ranker.py`: load `artifacts/ranker.txt` once at startup (`lgb.Booster(model_file=...)`), check `feature_names.json` equals `FEATURE_NAMES` (fail loudly if not); `rank(req, vm_df, tx_df)` → builds features via `features.py`, predicts, `pred_contrib=True`, returns sorted results with per-feature contributions.
  **Done when:** `/health` reports `model_loaded: true`.
- [x] **P3.9** (ME) `backend/app/routers/recommendations.py`: `POST /api/v1/recommendations` (saves the request, loads candidates + that material's transactions from the DB into DataFrames, ranks, saves `Recommendation` rows, returns `{request_id, results:[{rank, vendor_id, vendor_name, score, unit_price, total_price, lead_time_days, quality_score, ontime_rate, misses_deadline, in_stock, contributions}]}`); `GET /api/v1/recommendations/{request_id}`. A material with fewer than 2 candidates returns 422 with a clear message. Explanation endpoint comes in P4.
  **Done when:** a POST for "kardus 30x20x15, qty 100, deadline 3 days, weights 0.3/0.5/0.2" returns at least 5 vendors sorted by score descending; vendors with `lead_time_days > deadline` have `misses_deadline: true`.
- [x] **P3.10** (ME) Tests in `backend/tests/` (SQLite temp DB via dependency override): `test_health`, `test_vendor_crud`, `test_recommendation_order_and_flags`, `test_invalid_payload_422`, `test_features_same_function_as_training` (imports `FEATURE_NAMES` from the one module).
  **Done when:** `cd backend; ..\.venv\Scripts\python -m pytest -q` is all green.
- [ ] **P3.11** (YOU) Open http://localhost:8000/docs while I run `cd backend; ..\.venv\Scripts\python -m uvicorn app.main:app --port 8000`, and click **Try it out** on `POST /api/v1/recommendations`.
  **Done when:** you see a ranked JSON response. (This is also your first look at the Swagger documentation required by the course.)

**Gate P3:** tests green, Swagger works. Questions: (1) What happens on `POST /recommendations`, step by step? (2) Why is the model loaded once at startup and never retrained in the API?

---

# P4 — RAG explanation (Sun 08:00–10:30)

- [x] **P4.1** (ME) Write 6 policy notes in `backend/kb/policies/` (Indonesian, 3–5 sentences each, each starting with a one-line title): `urgent_orders.md`, `bulk_orders.md`, `quality_sensitive_items.md`, `reliability_threshold.md`, `new_vendor_trial.md`, `backup_vendor.md`. Add a header line in each: "Catatan ilustratif untuk prototipe, bukan kebijakan resmi Firaza." (these are our assumptions, not Firaza's real policy).
  **Done when:** six files exist, each with the disclaimer line.
- [x] **P4.2** (ME) `backend/app/rag/embeddings.py`: `embed_documents(texts)` and `embed_query(text)` using `genai.Client(api_key=...).models.embed_content(model=settings.gemini_embed_model, contents=[...], config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT" | "RETRIEVAL_QUERY"))`, batching up to 50 texts per call, retry up to 3 times with exponential backoff on rate-limit errors.
  **Done when:** embedding 3 sample sentences returns 3 vectors of equal length.
- [x] **P4.3** (ME) `backend/app/rag/kb.py`: build documents **from the database**: per vendor one `profile` doc (name, city, materials supplied with price range and typical lead time) and one `performance` doc (per vendor: transaction count, on-time percentage, average delay in days, average defect rate, share of last 6 months). Plus the 6 policy docs. Each document has metadata `{"type": "profile"|"performance"|"policy", "vendor_id": int | -1}` and a stable id.
  **Done when:** a dry run prints the number of documents (about 32×2 + 6 = 70) and shows one example of each type.
- [x] **P4.4** (ME) Chroma collection `firaza_kb` (`chromadb.EphemeralClient()`; contingency: FAISS index + a Python list of metadata if chromadb misbehaves). `rebuild_kb(db)` embeds all documents and adds them with their metadata. Called lazily on the first explanation request if the collection is empty, and by `POST /api/v1/kb/rebuild` (new `routers/kb.py`).
  **Done when:** `POST /api/v1/kb/rebuild` returns `{"documents": ~70}` and a count query on the collection matches.
- [x] **P4.5** (ME) `backend/app/rag/retrieval.py`: `retrieve(request, ranked_results)` → (a) for the top 3 vendors, fetch their `profile` and `performance` docs by metadata filter `vendor_id`, (b) semantic top 2 `policy` docs using the query text built from the request ("pesanan {qty} {material}, tenggat {deadline} hari, prioritas ..."), filtered by `type == "policy"`.
  **Done when:** a test request returns exactly 2 docs per top vendor and 2 policy docs; an urgent request (deadline 1–2) retrieves `urgent_orders` among the policies.
- [x] **P4.6** (ME) `backend/app/rag/explain.py`: build the context string (request, ranked table with numbers formatted once, top-3 feature contributions in words, retrieved docs). Prompt rules (system instruction, Indonesian): *"Gunakan hanya angka dan fakta dalam KONTEKS. Jangan menyebut vendor yang tidak ada di KONTEKS. Jika informasi tidak tersedia, tulis 'tidak tersedia'. Maksimal 120 kata. Struktur: (1) rekomendasi utama dan alasannya, (2) trade-off dibanding alternatif, (3) satu risiko atau catatan."* Call `models.generate_content(model=settings.gemini_gen_model, contents=prompt, config=types.GenerateContentConfig(temperature=0.2, system_instruction=...))`.
  **Done when:** a real call for the sample request returns Indonesian text that names the top vendor.
- [x] **P4.7** (ME) Fallback `fallback_explanation(request, results)`: a deterministic Indonesian template built from the same numbers (top vendor, price difference vs the cheapest in rupiah and percent, vendors that miss the deadline, top contributing features). Used when the API key is missing, the call fails/times out (20 s), or verification fails.
  **Done when:** with `GEMINI_API_KEY` unset, the endpoint still returns 200 with `source: "fallback"`.
- [x] **P4.8** (ME) `POST /api/v1/recommendations/{request_id}/explanation` → saves an `Explanation` row and returns `{text, source: "llm"|"fallback"|"fallback_unverified", sources: [doc ids]}`. If an explanation already exists for the request, return it (cache).
  **Done when:** calling it twice returns the same text without a second Gemini call (visible in logs).
- [x] **P4.9** (ME) Numeric verifier `verify(text, context)`: extract every number token with a regex, normalize thousand separators, and require each to appear in the context's set of numbers. On failure return `source: "fallback_unverified"` with the fallback text.
  **Done when:** unit tests cover a pass case and a case where an invented number triggers the fallback.
- [x] **P4.10** (ME) Tests with a mocked Gemini client: success path, API exception → fallback, invented number → `fallback_unverified`, missing key → fallback, cache hit.
  **Done when:** `pytest -q` is green.
- [x] **P4.11** (ME) `ml/eval_rag.py` (uses the running API): (a) **Recall@3** on 12 hand-written queries whose correct document id is known (e.g. "pesanan mendesak 1 hari" → `urgent_orders`; "vendor X ketepatan waktu" → vendor X performance doc), (b) **faithfulness** over 20 varied requests = share whose explanation passes the verifier with `source == "llm"`. Save `ml/reports/rag_eval.json`.
  **Done when:** the JSON exists with both numbers (target Recall@3 ≥ 0.9, faithfulness ≥ 0.9; report actual values honestly).

**Gate P4:** tests green, one real explanation read by you. Questions: (1) What is in the prompt and why does the LLM not choose the ranking? (2) What happens if Gemini is down?

---

# P5 — Frontend (Sun 10:30–12:30)

- [x] **P5.1** (ME) `frontend/api_client.py`: reads `BACKEND_URL` from `st.secrets` or the environment; `requests` wrapper with a 90-second timeout (free hosts sleep) and a clear error object; `wake_backend()` pings `/api/v1/health`.
  **Done when:** calling `wake_backend()` against the local backend returns True.
- [x] **P5.2** (ME) `frontend/app.py` (home): title, one-paragraph description, backend status indicator ("Backend siap" / "Membangunkan backend…") and a short "how to use" list. `st.set_page_config(layout="wide")`.
  **Done when:** `cd frontend; ..\.venv\Scripts\python -m streamlit run app.py` opens and shows the status.
- [x] **P5.3** (ME) `pages/1_Vendors.py`: table of vendors; form to add; select a row to edit or delete; success/error messages from the API.
  **Done when:** you can add a vendor and see it after a page reload.
- [x] **P5.4** (ME) `pages/2_Materials_Prices.py`: choose a material → list vendor offers (price, bulk price, MOQ, lead time, stock, quality); add/edit an offer.
  **Done when:** editing a price persists after reload.
- [x] **P5.5** (ME) `pages/3_Transactions.py`: list with vendor/material filters; add a transaction form.
  **Done when:** a new transaction appears in the list.
- [x] **P5.6** (ME) `pages/4_Recommend.py` — the star page: form (material select, qty, deadline days, three sliders price/speed/quality), button **Cari rekomendasi** → calls `/recommendations`, shows the ranked table (rank, vendor, unit price, total, lead time, quality, on-time, "melewati tenggat" flag), a Plotly bar chart of total price with the rank-1 vendor highlighted, and a second Plotly bar chart of the top-3 feature contributions for the winner. Then calls the explanation endpoint with a spinner and shows the text with a badge (`LLM` / `Fallback`).
  **Done when:** the example request (kardus, 100, 3 days) shows ranking, charts, and an Indonesian explanation.
- [x] **P5.7** (ME) Edge states: empty backend, API error, 422 message shown in plain Indonesian, explanation still loading.
  **Done when:** stopping the backend shows a friendly message, not a Python traceback.
- [ ] **P5.8** (YOU) Click through all four pages once and tell me anything confusing (two minutes).
  **Done when:** I have your notes; I apply only small fixes.

**Gate P5:** full local flow works. Questions: (1) Why does the UI know nothing about the model? (2) What does the user see if the backend is asleep?

---

# P6 — Deploy and harden (Sun 12:30–15:00, code freeze 15:00)

- [ ] **P6.1** (ME) Seed Neon from local: run `seed.py --target prod`.
  **Done when:** it prints counts, and the same counts show in Neon's table viewer.
- [x] **P6.2** (ME) Pre-deploy check: `backend/requirements.txt` has pinned versions; `git status` is clean after commit; `.env` and `.gitignore`d files are not tracked (`git ls-files | findstr .env` returns nothing). Commit and push (with your "go").
  **Done when:** latest commit is on GitHub.
- [ ] **P6.3** (YOU) Render: sign in at https://render.com with GitHub → **New → Web Service** → pick the repo → settings:
  Root Directory `backend` · Runtime Python · Build Command `pip install -r requirements.txt` · Start Command `uvicorn app.main:app --host 0.0.0.0 --port $PORT` · Instance type **Free** · Environment variables: `PYTHON_VERSION=3.12.7`, `DATABASE_URL=<your Neon string>`, `GEMINI_API_KEY=<key>`, `GEMINI_GEN_MODEL`, `GEMINI_EMBED_MODEL`.
  **Done when:** the deploy log ends with "Your service is live".
- [ ] **P6.4** (ME) Verify the live API: `GET https://<service>.onrender.com/api/v1/health` returns `model_loaded: true`; `POST /api/v1/recommendations` returns results; `POST .../explanation` returns text. (First call after sleep can take about a minute.)
  **Done when:** all three succeed; I record the URL in `README.md`.
- [ ] **P6.5** (YOU) Streamlit Community Cloud: https://share.streamlit.io → sign in with GitHub → **Create app** → repo `abidayn/firaza-vendor-assistant`, branch `main`, main file `frontend/app.py` → **Advanced settings → Secrets**: `BACKEND_URL = "https://<service>.onrender.com"` → Deploy. (Requirements are read from `frontend/requirements.txt`.)
  **Done when:** the app URL opens and shows "Backend siap".
- [ ] **P6.6** (ME) End-to-end test on the live URL, 10 scenarios (different materials, deadlines 1–10, weights at extremes, qty 20 and 500) with a table of results in `docs/E2E_TEST.md` (scenario, expected behavior, pass/fail).
  **Done when:** 10 rows filled; any failure is fixed or listed as a known issue.
- [ ] **P6.7** (ME) Error-path checks on live: unknown material id → clean 4xx JSON; Gemini key removed in a local run → fallback explanation; backend stopped → frontend shows the friendly message.
  **Done when:** three results recorded in `docs/E2E_TEST.md`.
- [x] **P6.8** (ME) Security sweep: scan the repo history and working tree for strings that look like the key (`AIza`), the Neon host, or `postgresql://`; confirm `.env` was never committed.
  **Done when:** zero matches outside `.env.example` placeholders.
- [x] **P6.9** (ME) *Only if Render runs out of memory:* replace Chroma with FAISS (`faiss-cpu`, MIT) behind the same `retrieve()` interface, redeploy, and note it in the Project Brief.
  **Done when:** the live explanation call works again (or this task is marked "not needed").
- [ ] **P6.10** **CODE FREEZE at 15:00.** After this, only documentation and the videos change. Tag the commit: `git tag v1.0-submission`.
  **Done when:** the tag exists and is pushed.

**Gate P6:** two live URLs work from a phone browser too. Questions: (1) Where does the Gemini key live in production? (2) Why does the first request after idle take long?

---

# P7 — Documentation, videos, submit (Sun 15:00–21:00)

Parallel tracks: I write documents while you record.

## P7-A Documents (ME)
- [x] **P7.1** (ME) Software inventory and licenses: `pip-licenses --format=markdown --with-urls --output-file=docs/SBOM.md` (from the venv) and flag anything GPL/AGPL/LGPL/MPL/EPL. Write `docs/LICENSE_NOTES.md` listing each flagged package (expected: `certifi` MPL-2.0, `tqdm` MPL-2.0 AND MIT, possibly others from chromadb), why it is transitive and not avoidable, and that the project code itself is MIT. Include the Gemini API terms note.
  **Done when:** both files exist and every flagged package has a one-line justification.
- [x] **P7.2** (ME) Final `README.md`: what it is, live URLs, architecture diagram (ASCII), install and run (backend, frontend, seed, retrain), environment variables (names only), API overview with the `/docs` link, test command, metrics summary (copied from `ml/reports/metrics.md` and `rag_eval.json`), limitations (synthetic data, no login, free-tier cold start), citations (LightGBM, LambdaMART, RAG, TOPSIS, NDCG, Gemini API), license.
  **Done when:** a fresh reader could run the project from the README alone (I dry-run the commands).
- [x] **P7.3** (ME) `docs/USER_GUIDE.md` (Indonesian, with the 4 pages and the main flow) and `docs/ARCHITECTURE.md` (diagram, data flow, table list, why decoupled).
  **Done when:** both exist.
- [ ] **P7.4** (YOU) Put the **Project Brief template** in `submission/brief/` (export the Google Doc as `.docx` and drop it in, or tell me where it is). It is not in this folder yet and I cannot open the Google link.
  **Done when:** the file is in `submission/brief/`.
- [x] **P7.5** (ME) Fill the Project Brief from the template using `docs/`, `ml/reports/`, and the live URLs; update deviations from the Project Plan (single repo, Gemini embeddings instead of e5, no Docker, Streamlit + FastAPI); leave screenshot placeholders where you must paste images. Export PDF if the form requires it.
  **Done when:** the brief has no template instruction text left and lists every required section.
- [ ] **P7.6** (YOU) Take screenshots (Win+Shift+S) of: the Recommend page result, Swagger `/docs`, the metrics table, the Vendors page. Save to `submission/brief/img/` and tell me.
  **Done when:** 4 images are there; I insert them.
- [x] **P7.7** (ME) Slides: write `submission/slides/outline.md` following the mandatory 6-part outline (background, why this project, similar solutions and what they lack, implementation, results, documentation and usage), 10–12 slides, one idea per slide, then generate `submission/slides/firaza_pitch.pptx`.
  **Done when:** the .pptx opens and has the 6 sections.
- [x] **P7.8** (ME) Write `submission/videos/demo_script.md` (3 minutes, the AI feature on the live app: enter a request → ranking → explanation → show the fallback and the Swagger endpoint) and `submission/videos/presentation_script.md` (10 minutes, Indonesian, timed per slide, sections: intro 1:00, problem 1:30, solution and architecture 2:00, ML ranker and evaluation 2:00, RAG 1:30, live demo 1:30, limitations and closing 0:30).
  **Done when:** both scripts exist and total 3:00 and 10:00 when read at normal pace.

## P7-B Recording and submission (YOU)
- [ ] **P7.9** (YOU) Record the **demo video** (about 3 min, screen only is fine, narrate in Indonesian). Windows tip: **Win+G → Capture**, or Zoom/Meet "record" with screen share. Save to `submission/videos/demo.mp4`.
  **Done when:** it plays with sound and shows the live URL, a ranking, and the explanation.
- [ ] **P7.10** (YOU) Record the **10-minute presentation video**: camera **on** with your face visible, slides shared, Indonesian, follows the script. Zoom local recording or Google Meet recording both work. Upload to Google Drive or YouTube (unlisted) and set the link to "anyone with the link can view".
  **Done when:** the link opens in a private window.
- [x] **P7.11** (ME) Final checklist `submission/checklist.md` mapping every course requirement to evidence (Main Quest items, Side Quest RAG, licenses, API key safety, live URL, persistent DB, Swagger, tests, SBOM, README, video, repo). Verify each link opens.
  **Done when:** every row has a link or file path, no blanks.
- [ ] **P7.12** (YOU) Open the **Form Pengumpulan Final Deliverables** (link in the playbook), paste the links (Project Brief, GitHub repo, live URLs, videos, slides), and **submit** before 21:00. After submitting, do not modify any file or video.
  **Done when:** you have the submission confirmation.
- [ ] **P7.13** (YOU) Fill the **360 Feedback** form (window 20–24 Nov) and check that your advisor session and mid-checkpoint report are recorded (I cannot see these).
  **Done when:** both are done or you know what is missing.

**Gate P7 = Done.**

---

## Definition of done (course requirements)

- [ ] Model trained by us on our data, with preprocessing (P1–P2); no pretrained model or AutoML as core
- [ ] First feature is the ranking model, not a raw LLM call (P2, P3.9)
- [ ] RAG system: embedding + vector DB + generation, integrated in the app (P4)
- [ ] REST API with interactive documentation (P3, Swagger `/docs`)
- [ ] Data persisted in a real database; live URL, not localhost (P3, P6)
- [ ] Errors handled without crashing; AI failure has a fallback (P4.7, P6.7)
- [ ] API key only in environment variables; not in git (P6.8)
- [ ] Only permissive licenses, SBOM present, exceptions documented (P7.1)
- [ ] Citations for libraries, models, methods; data self-generated and documented (P1.6, README)
- [ ] Open source MIT repo with real commit history (P0.10)
- [ ] Project Brief, usage guide or demo video, slides, 10-minute video with face on camera (P7)
- [ ] Submitted before the deadline (P7.12)

## Known limitations (state them honestly in the brief and the video)
- All data is synthetic; labels come from a function we wrote, so results prove the pipeline works, not real-world accuracy.
- No user login; free-tier hosting sleeps when idle.
- Policy documents in the knowledge base are illustrative assumptions, not Firaza's real policy.
