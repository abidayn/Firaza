# Firaza Vendor Recommendation & Procurement Assistant — Pre-Read

**Audience:** you — a developer who is new to ML/AI and knows only the basics of RAG.
**Goal:** after reading, you can explain *what* we are building, *why each piece exists*, *where the AI/ML is*, and *what you will work on* — so that when I (the coding agent) write code, you can follow it, question it, and defend it.
**Reading time:** ~40 minutes. Read sections 1–5 first (the picture), then 6–8 (the concepts), then 9–12 (the work).

> Status note: the project folder currently contains only the planning documents (playbook, template, use case, Project Plan). **No application code exists yet.** The schedule in section 10 is built around that fact.

---

## 0. Working agreement — how we build this without "blind vibe coding"

Because I will write much of the code, the risk is that you end up with a project you cannot explain. The assessors grade a presentation video, a project brief, and Q&A-style understanding, so understanding is part of the deliverable.

For every phase, we follow this loop:

1. **Brief** — I explain the concept in plain words (what, why, how it connects to the rest).
2. **Predict** — I ask you one or two questions ("what do you expect the baseline's score to be and why?").
3. **Build** — I write the code in small steps, each with a short "what this does and why" note.
4. **Explain-back** — you explain the step in your own words (a sentence or two is enough).
5. **Break it** — we deliberately change something (remove a feature, shuffle labels) to see what happens. This is where ML intuition actually forms.

Rules of thumb:
- Ask "why" any time. A good answer from me should fit in a few sentences; if it doesn't, tell me it's too dense.
- I will not move to the next phase until you can answer that phase's **checkpoint questions** (listed in section 9).
- Small commits, one idea per commit, so the git history doubles as your learning log (and as proof of your own work for the assessors).

---

## 1. The 60-second version

Firaza is a small online shop (towels, prayer mats, gift hampers). To pack orders, it buys supplies — boxes, ribbon, packaging, embroidery materials — from many vendors. Today the owner chooses vendors from memory and a spreadsheet.

We build a **web app that answers: "I need 100 boxes in 3 days. Which vendor should I use, and why?"**

It has three layers:

| Layer | What it does | Type of work |
|---|---|---|
| **Web app + database** | Store vendors, prices, lead times, history; show forms and pages | Normal software engineering |
| **Ranking model** | Gives every candidate vendor a score for *this specific request* and sorts them | **Machine learning** (the core of your project) |
| **Explanation (RAG)** | An LLM reads vendor facts + the model's reasoning and writes the "why" in plain Indonesian | **Generative AI** (RAG, which you already know) |

The app only **advises**. The owner makes the final decision.

---

## 2. The problem in plain words

- ~99% of Firaza's sales are online (Shopee, TikTok Shop, website, WhatsApp for bulk orders).
- Procurement (buying supplies) is done by the **owner personally**; vendor info lives in a spreadsheet and in the owner's head.
- **Cheapest ≠ best.** A cheap vendor may deliver late, send poor quality, or have a history of delays. A slightly pricier vendor can be the better choice when the order is urgent.
- With few vendors this is manageable by hand. As vendors, materials, and transactions grow, comparing everything consistently becomes hard, and nobody except the owner can do it.

**The gap we close:** from "depends on the owner's memory" to "centralized data + a consistent, explainable recommendation anyone on the team can use."

The use case document defines success as (paraphrased): admin can manage vendor data via web; the system stores prices, lead time, quality, history; a user can enter a procurement need; an AI model ranks vendors; the result is available through an inference API; generative AI explains the recommendation; the whole flow works end-to-end; and the ranking method has documented evaluation.

---

## 3. The end product — what it looks like and how it is used

### 3.1 Who uses it
- **Owner / staff (user):** enters a need, reads the ranking and explanation, decides.
- **Admin (probably the same person):** maintains vendor, material, price, and transaction data.

### 3.2 The screens (5 pages, built in Streamlit)

```
┌─ Sidebar ─────────────┐   ┌─ Main area ─────────────────────────────────────┐
│ Dashboard             │   │                                                 │
│ Vendors          (CRUD)│  │  Page content                                   │
│ Materials & Prices(CRUD)│ │                                                 │
│ Transactions     (CRUD)│  │                                                 │
│ ► Recommend vendors   │   │                                                 │
└───────────────────────┘   └─────────────────────────────────────────────────┘
```

1. **Dashboard** — summary counts, recent requests.
2. **Vendors** — add / edit / delete vendors and their contact/notes.
3. **Materials & Prices** — which vendor sells which material, price tiers, lead time, MOQ, availability, quality score.
4. **Transactions** — simple history: when ordered, how many, promised vs actual delivery days, defects.
5. **Recommend vendors** — *the star page*: enter a need → get ranking + comparison + explanation.

### 3.3 A worked example (illustrative numbers)

**Request** entered on page 5:

> Material: corrugated box (30×20×15) · Quantity: **100** · Needed within: **3 days** · Priority sliders: price 30% / speed 50% / quality 20%

**What the system knows about the candidates** (from the database):

| Vendor | Unit price | Typical lead time | Quality (1–5) | On-time rate (history) |
|---|---|---|---|---|
| A | Rp 2,300 | 2 days | 4.5 | 96% |
| B | Rp 2,000 | 5 days | 4.0 | 85% |
| C | Rp 2,150 | 3 days | 3.8 | 90% |
| D | Rp 1,900 | 7 days | 3.5 | 78% |

**The ranking model outputs** a score per vendor and the app sorts them (scores illustrative):

| Rank | Vendor | Model score | Total for 100 units |
|---|---|---|---|
| 1 | A | 3.7 | Rp 230,000 |
| 2 | C | 2.9 | Rp 215,000 |
| 3 | B | 1.4 | Rp 200,000 |
| 4 | D | 0.6 | Rp 190,000 |

**Why A wins** (this is what the model's internals say — "feature contributions"): deadline slack is positive (+1 day), on-time rate is high, quality is highest; price is a small negative. B and D would arrive *after* the 3-day deadline, so they get pushed down despite being cheaper.

**The generated explanation** (RAG + LLM, in Indonesian), shown under the table, e.g.:

> *Vendor A direkomendasikan karena satu-satunya yang memenuhi tenggat 3 hari dengan margin 1 hari, dengan tingkat ketepatan waktu 96% dan kualitas tertinggi (4,5). Biayanya Rp 30.000 (15%) lebih mahal dibanding Vendor B, namun Vendor B diperkirakan tiba 2 hari setelah tenggat. Vendor C memenuhi tenggat tepat waktu tetapi tanpa margin dan dengan kualitas lebih rendah.*

The model's job was to **order** the vendors. The LLM's job was to **put words to that order using real numbers**. The LLM must not decide the ranking.

### 3.4 What happens when you click "Recommend" (step by step)

1. **Streamlit** sends the request (material, qty, deadline, weights) to the **FastAPI** backend: `POST /api/v1/recommendations`.
2. The backend **loads candidate vendors** for that material from **PostgreSQL**.
3. For each candidate, it **builds features** (price vs median, lead-time slack vs deadline, on-time rate from history, quality, MOQ ratio, …). This is the *preprocessing pipeline* — the same code used during training.
4. The **trained ranking model (LightGBM)** scores every candidate.  ← **ML happens here**
5. The backend sorts by score and also gets each feature's **contribution** to each score ("why this score").
6. The backend **retrieves** relevant text (vendor profile, history summary, procurement policy) from **ChromaDB** using embeddings.  ← **RAG retrieval**
7. It builds a **prompt**: retrieved context + ranking + contributions + strict rules ("use only this context, don't invent numbers").
8. It calls the **Gemini API**, receives the explanation.  ← **RAG generation**
9. It **saves** the recommendation + explanation in the DB and returns JSON; Streamlit renders the table, chart, and text.

Fallback: if Gemini is rate-limited or down, the backend returns a template-based explanation built from the same numbers, so the app never crashes.

---

## 4. Architecture

```
                    ┌──────────────────────┐
                    │  Streamlit (frontend)│   ← what the user sees
                    └──────────┬───────────┘
                               │ HTTP / JSON  (Swagger-documented REST API)
                    ┌──────────▼───────────┐
                    │  FastAPI (backend)   │   ← the "brain" coordinator
                    └─┬────────┬─────────┬─┘
        CRUD / history│        │ rank    │ explain
          ┌───────────▼──┐ ┌───▼──────┐ ┌▼───────────────────────────┐
          │ PostgreSQL   │ │ LightGBM │ │ RAG                        │
          │ (tables)     │ │ ranker   │ │ embeddings → ChromaDB      │
          │ vendors,     │ │ (a file  │ │ → prompt → Gemini API      │
          │ prices,      │ │ loaded   │ └────────────────────────────┘
          │ transactions │ │ in memory)│
          └──────────────┘ └──────────┘
```

Key ideas:
- **Decoupled:** frontend and backend are separate repos/deployments that talk over HTTP. (A course requirement.)
- **Two kinds of data storage:** PostgreSQL stores **structured records** (rows/columns). ChromaDB stores **vectors** (numbers that represent text meaning) for semantic search. The Chroma index is *derived* from the database and can be rebuilt on startup.
- **The model is just a file** (saved after training) that the backend loads at startup. "Inference" = running that loaded model on new inputs. It is fast (milliseconds) and needs no GPU.
- **Training happens offline** (in a notebook/script), once. The running app never trains.

---

## 5. Tech stack — what each tool is *for*

| Tool | Category | What it is | Why it's here | Analogy for a dev |
|---|---|---|---|---|
| **Python** | Language | The language of ML | Everything AI-related is easiest here | — |
| **pandas / NumPy** | Data | Tables (DataFrames) and fast math arrays | Clean data, compute features, EDA | Like SQL/LINQ + Excel inside Python |
| **Faker** | Data | Generates fake names/values | Part of synthetic data generation | Test-data seeder |
| **scikit-learn** | ML toolkit | Standard ML library: preprocessing, splits, metrics, simple models | Build the preprocessing pipeline, baselines, NDCG, cross-validation | The "standard library" of classic ML |
| **LightGBM** | ML model | Fast gradient-boosted decision-tree library with a built-in **ranking** mode | Our trained ranking model | An optimized engine that *learns* the scoring function from examples |
| **Jupyter / Colab** | Environment | Notebooks: run code cell-by-cell with outputs | Experiment and explore before writing production code | A REPL with memory and charts |
| **sentence-transformers + multilingual-e5-small** | Embeddings | A small open model that turns text into a vector of numbers | Makes text searchable by *meaning* (works for Indonesian) | A "meaning hash" where similar text lands close together |
| **ChromaDB** | Vector DB | Stores vectors, returns nearest ones | Retrieval step of RAG | An index for "find similar" instead of "find equal" |
| **Gemini API** | LLM | Google's hosted language model | Writes the final explanation | A remote function: text in → text out |
| **FastAPI** | Backend | Python web framework; auto-generates API docs at `/docs` | The REST API (CRUD + `/recommendations`) | Express/Spring, but Python and type-checked |
| **Pydantic** | Validation | Declares input/output shapes; rejects bad data | Request validation (course "schema validation" bonus) | Zod / DTOs |
| **PostgreSQL + SQLAlchemy** | Database | Relational DB + Python ORM | Persistent data (required: not in-memory) | Standard SQL DB + ORM |
| **Streamlit** | Frontend | Turns a Python script into a web UI | Fast UI for a solo developer; the course's minimum for individual Gen AI | A UI framework where you never write HTML/JS |
| **Plotly** | Charts | Interactive charts | Comparison bar/radar chart | Charting lib |
| **pytest / httpx** | Testing | Test runner / HTTP client | API and pipeline tests | Jest/supertest |
| **Docker + Render / Hugging Face Spaces / Streamlit Cloud / Neon** | Deployment | Containers + free hosting + free hosted Postgres | Required: a live URL, not localhost | Standard deploy path |
| **Git + GitHub** | Version control | — | Proof of work for assessors | — |
| **pip-licenses / CycloneDX** | Compliance | Lists dependency licenses / builds an SBOM | Course rule: only permissive licenses, documented | License audit |

Plain-English glossary of the buzzwords above is in section 13.

---

## 6. ML primer for first-timers

### 6.1 Rules vs learning
- **Traditional code:** *you* write the logic. `if price < X and days < Y: good`.
- **Machine learning:** you give the computer many examples of *inputs → correct outputs*, and it works out the logic itself. The learned logic is a **model**.

Why bother here? Hand-written rules get messy ("how much is a day of delay worth vs Rp 50?") and the right trade-off changes by situation (urgent vs not). A model can learn those trade-offs from examples, and we can measure how well it does.

### 6.2 Tabular data: features and labels
Everything we do is **tabular** — rows and columns, like a spreadsheet. No images, no audio, no neural networks (so: **no deep learning**).

- **Feature:** an input column the model may look at (price relative to peers, lead-time slack, on-time rate…).
- **Label:** the "right answer" column the model learns to predict. In our ranking problem: a relevance grade **0 (bad choice) … 4 (excellent choice)** for each vendor in each request.

### 6.3 Training, model, inference
- **Training:** the algorithm looks at lots of (features → label) rows and adjusts itself to reduce mistakes.
- **Model:** the trained result. For us, a saved file.
- **Inference:** using the trained model on new data (a real request) to get predictions.

### 6.4 Overfitting, train/test split, leakage — the three ideas that matter most
- **Overfitting:** the model memorizes training examples instead of learning general patterns. Looks perfect on data it has seen, fails on new data. Like a student memorizing last year's exam.
- **Train/test split:** hide a portion of data from the model during training and evaluate on it afterwards. This is the honest exam.
- **Leakage:** the exam secretly shares information with the training. In ranking, if the *same request* appears in both train and test, the score is inflated. So we split **by request (query group)**, never by individual rows.

### 6.5 What LightGBM is (and isn't)
- A **decision tree** is a flowchart the algorithm builds itself: "is slack ≥ 0? → is on-time rate > 90%? → …". One tree is weak.
- **Gradient boosting** builds many small trees *in sequence*, each one correcting the previous ones' mistakes, and sums them up. That's **LightGBM** (also XGBoost, CatBoost). It is the go-to method for tabular data.
- You do **not** need the math to use it responsibly. You do need to understand the inputs (features), the target (labels/groups), the metric (NDCG), and the pitfalls (6.4).

### 6.6 Why "ranking" instead of "predict a number"
Three common ML tasks:
- **Classification:** pick a category (spam / not spam).
- **Regression:** predict a number (price tomorrow).
- **Ranking ("learning to rank"):** order a list of candidates for a given query so the best ones are on top.

We don't care if vendor A's score is 3.7 or 3.9 — only that A sits above C. Ranking models are trained for exactly that. The algorithm is called **LambdaRank / LambdaMART**; in LightGBM it's `LGBMRanker` with objective `lambdarank`.

**Query groups:** the model needs to know which rows belong together. One *request* = one group; its candidate vendors are the rows. You pass group sizes to the trainer ("the first 6 rows are request 1, the next 5 are request 2…").

### 6.7 How we measure a ranking: NDCG (worked example)
**Question NDCG answers:** "Did the genuinely best vendors end up near the top?" Score 0–1; 1 = perfect.

Suppose the true relevance grades are A=4, C=3, B=1, D=0, and the model ranks them **B, A, C, D**.

- Each position gets a discount: position 1 → ÷1, position 2 → ÷1.585, position 3 → ÷2, position 4 → ÷2.32.
- **DCG** (model's order) = 1/1 + 4/1.585 + 3/2 + 0 = 1 + 2.524 + 1.5 = **5.024**
- **Ideal DCG** (best possible order A, C, B, D) = 4/1 + 3/1.585 + 1/2 + 0 = 4 + 1.893 + 0.5 = **6.393**
- **NDCG = 5.024 / 6.393 ≈ 0.786**

(LightGBM's default gain uses 2^grade − 1 instead of the raw grade, so exact numbers differ, but the idea is the same. "NDCG@3" = only look at the top 3.)

**Baselines** (the "dumb competitors" the model must beat, otherwise ML added nothing):
1. **Cheapest first.**
2. **Weighted sum:** normalize each attribute to 0–1, multiply by weights, add up.
3. **TOPSIS:** a classic decision-science method — prefers the option closest to the "ideal" and farthest from the "worst" across all criteria.

### 6.8 Explaining the model
For each prediction, LightGBM can return **feature contributions**: how much each feature pushed this vendor's score up or down. That's a number list like `slack +1.2, on_time +0.8, quality +0.6, price −0.3`. We pass these to the LLM, so its explanation reflects what the **model** actually used — not what the LLM imagines.

### 6.9 Synthetic data and the honest limitation
Firaza gave **no real data**, so we generate fake-but-realistic data with a script (fixed random seed → reproducible).

**The catch (circularity):** the labels (0–4) come from a utility function *we* write. A model trained on them partly relearns *our* function. That's acceptable for a prototype if we:
- vary the preference weights per request (so the model must handle trade-offs),
- add noise to the labels (real judgments are not perfectly consistent),
- compare against baselines (the model should do better than simple rules, especially when preferences differ),
- state the limitation openly: results show the pipeline works on simulated data; they are **not** proof of real-world accuracy.

Say this yourself in the presentation. Assessors read it as maturity, not weakness.

### 6.10 Training/serving consistency (a classic trap)
The features at training time and at request time **must be computed by the same code**. If training used "price relative to median" and the API computes it slightly differently, the model silently gives bad answers. That's why preprocessing is one reusable module imported by both the training script and the API.

---

## 7. RAG in this project (you know the basics — here's the mapping)

**Standard RAG:** retrieve relevant text → give it to an LLM with the question → LLM answers *grounded* in that text.

**Ours:**

| RAG step | In this project |
|---|---|
| **Documents** | Vendor profiles; per-vendor/per-material performance summaries (on-time rate over 90 days, average delay, defect rate, price trend); short procurement policy notes ("for urgent orders prioritize lead time") — all synthesized |
| **Chunking** | One chunk per vendor profile / per performance summary / per policy rule (short, self-contained) |
| **Embedding** | `multilingual-e5-small` turns each chunk into a vector. Gotcha: E5 models expect the prefix `"passage: "` on documents and `"query: "` on queries |
| **Vector store** | ChromaDB collection; rebuilt from the DB at startup |
| **Retrieval** | Query = e.g. "Why recommend Vendor A for corrugated boxes, urgent?" → top-k similar chunks |
| **Prompt** | Retrieved chunks + the model's ranking + feature contributions + rules |
| **Generation** | Gemini API |
| **Guardrails** | "Use only the context." Low temperature. Indonesian output. After generation, check that the numbers in the text match the data. If the API fails → template fallback |

**Important design point:** retrieval alone doesn't choose the vendor — the **ranking model** does. RAG adds *context and language*. Keep this boundary clear, because the course forbids making a raw LLM call "the first feature": our first feature is the trained model; the LLM explains it.

**RAG quality metrics we'll report:**
- *Retrieval:* Recall@3 — in a set of test questions where we know the right chunk, how often is it in the top 3?
- *Faithfulness:* do the claims and numbers in the generated text match the data? (automated number check + manual review of ~30 scenarios)

---

## 8. Data design

### 8.1 Database tables (PostgreSQL)

| Table | Key columns |
|---|---|
| `vendors` | id, name, city, notes |
| `materials` | id, name, category (packaging, ribbon, embroidery thread…), unit |
| `vendor_materials` | vendor_id, material_id, price tiers (qty → unit price), MOQ, typical lead time (days), availability, quality score |
| `transactions` | id, vendor_id, material_id, qty, unit_price, ordered_at, promised_days, actual_days, defect_rate |
| `procurement_requests` | id, material_id, qty, deadline_days, weight_price, weight_speed, weight_quality, created_at |
| `recommendations` | id, request_id, vendor_id, rank, score, contributions (JSON) |
| `explanations` | id, request_id, text, source (llm / fallback), created_at |

### 8.2 Training dataset (offline, generated by a script — separate from the tables above)
One row = one *(request, candidate vendor)* pair.

| Column group | Examples |
|---|---|
| Group id | `request_id` (which query this row belongs to) |
| Features | unit price, price ÷ median price among candidates, avg lead time, p90 lead time, slack = deadline − lead time, quality score, on-time rate, defect rate, MOQ ÷ quantity, availability, history count, recency |
| Label | relevance grade 0–4 (from the utility function + noise, quantized) |

### 8.3 Scale (small on purpose)
~30–40 vendors, 12–15 materials, ~2,000–3,000 transactions over ~18 months, a few thousand simulated requests for training. Small data is fine because the model is small and the goal is a working, honest pipeline.

---

## 9. What you will build — work breakdown with tags

Tags: **[ENG]** normal engineering · **[ML]** machine learning · **[GENAI]** RAG/LLM.

| Phase | Work | Tag | Checkpoint — you should be able to answer |
|---|---|---|---|
| **1. Data** | Generator script for vendors/transactions; preprocessing pipeline; basic EDA; seed DB | ML/ENG | What is a feature vs a label? Why a fixed random seed? What does each preprocessing step fix? |
| **2. Model** | Build query groups + labels; baselines (cheapest, weighted-sum, TOPSIS); train LGBMRanker; evaluate NDCG; feature contributions; save model | **ML** | Why group split by request? What does NDCG@3 = 0.85 mean? Why is beating a baseline the real test? What is the circularity limitation? |
| **3. Backend** | FastAPI app, DB models, CRUD endpoints, `/recommendations`, validation, tests, Swagger | ENG (+ML serving) | What happens on `POST /recommendations`? Where is the model loaded and why not retrained? What is training/serving skew? |
| **4. RAG** | Knowledge base, embeddings, ChromaDB, prompt, Gemini call, guardrails, fallback, eval | **GENAI** | What goes into the prompt and why? What stops hallucinated numbers? What happens if Gemini fails? |
| **5. Frontend** | Streamlit pages: CRUD, request form, comparison + explanation | ENG | How does the UI know nothing about the model? (It only calls the API.) |
| **6. Ship** | Deploy (backend, frontend, DB), E2E tests, secrets, license audit/SBOM, README | ENG | Where does the API key live? Why must the live URL not be localhost? |
| **7. Deliver** | Project Brief, demo video of the AI feature, slides, 10-min presentation video, submit | — | Can you explain every box in the architecture diagram from memory? |

**Minimum lovable core** (if time forces cuts): data → ranker + evaluation → one `/recommendations` endpoint → RAG explanation with fallback → a Streamlit page with the form and results → CRUD for vendors and prices → deploy.

---

## 10. Reality check on the schedule (as of 17 Nov 2026)

- Final deliverables are due **22 Nov 2026, 23:59 WIB**. That is **about 5 days**.
- The original plan assumed a 3-week build starting 3 Nov. No code has been written, so the plan must be **compressed**, not followed literally.

**Compressed plan (suggestion):**

| Day | Focus |
|---|---|
| 17 Nov | Phase 1 + start Phase 2: data generator, preprocessing, baselines |
| 18 Nov | Phase 2: train ranker, evaluate, save model + model card |
| 19 Nov | Phase 3: FastAPI + DB + `/recommendations` + basic CRUD (vendors, prices) |
| 20 Nov | Phase 4 + 5: RAG explanation with fallback; Streamlit pages; first deploy |
| 21 Nov | Fix, test, deploy stable, README/SBOM; record demo video; start Project Brief |
| 22 Nov | Slides, 10-min presentation video, submit (aim before 18:00) |

**Cut list (drop in this order if behind):** charts → request history/CSV export → login → transaction CRUD UI (seed via script instead) → polish. **Do not cut:** trained ranker + evaluation, `/recommendations` API, RAG explanation (with fallback), a persistent database, a live URL, the licenses/SBOM, the videos.

**Other process items to double-check yourself** (I can't see these): whether your advisor session (required, at least 45 min) happened, whether you submitted the mid-checkpoint progress report (window was 29 Oct–1 Nov), and the 360-feedback form (20–24 Nov).

---

## 11. Rules and compliance checklist (from the playbook)

- ☐ Model is **trained by you** — no pretrained models from TensorFlow Hub-like sources, no AutoML, not "just call the LLM".
- ☐ Preprocessing step before the model.
- ☐ Every dataset/library/model **cited** with its license.
- ☐ **API key in an environment variable / secrets manager**, never in code or git.
- ☐ Only permissive licenses (MIT / Apache-2.0 / BSD). **No** GPL, AGPL, LGPL, MPL, EPL. Watch transitive dependencies (e.g. `psycopg2` is LGPL → use `asyncpg`; `certifi` is MPL and is hard to avoid → document and confirm with Dicoding).
- ☐ Repo is **open source (MIT)**; dependencies listed in README/SBOM.
- ☐ No personal data, no Firaza confidential data in the public repo.
- ☐ Live URL; data persisted in a real DB; app handles errors without crashing.
- ☐ Paid APIs need Dicoding's approval first — stay on free tiers.
- ☐ No forking someone else's project; write your own code.
- ☐ Deliverables: Project Brief (official template), usage guide or demo video, slides (6-part outline), 10-min presentation video with your face on camera, Indonesian language.

---

## 12. Questions you must be able to answer (Q&A / video prep)

1. Why a trained ranking model instead of asking an LLM "which vendor is best"?
2. What are your features and why those? What is your label and where does it come from?
3. What does NDCG@3 measure? What did you compare against, and what was the result?
4. Your data is synthetic — why should anyone trust the result? (Answer with the limitation honestly.)
5. What exactly does the LLM do, and what stops it from inventing numbers?
6. What happens if the Gemini API fails or is rate-limited?
7. How does the model get from a notebook to the API? What is "inference"?
8. How would this change with Firaza's real data?
9. Where are the API keys? How do you know no secret is in the repo?
10. What would you improve next? (More real data, feedback loop from owner's actual choices, price-trend features, etc.)

---

## 13. Glossary (buzzwords decoded)

- **AI / ML / DL:** AI is the broad field; ML is "learn from data"; DL is ML using big neural networks. We only use classic ML (+ an LLM via API).
- **Model:** the trained program/file that makes predictions.
- **Feature / label:** input column / correct-answer column.
- **Training / inference:** learning phase / using the model.
- **Overfitting / leakage:** memorizing instead of learning / test info sneaking into training.
- **Gradient boosting / LightGBM:** many small decision trees built in sequence; a fast library for it.
- **Learning to rank / LambdaRank:** training a model to order candidates well.
- **NDCG:** ranking quality score, 0–1.
- **Baseline:** simple method the model must beat.
- **TOPSIS:** classic multi-criteria decision method, used as a baseline.
- **Synthetic data:** artificially generated data.
- **EDA:** exploratory data analysis — looking at distributions and relationships before modeling.
- **Pipeline (sklearn):** a chained, reusable sequence of preprocessing steps.
- **LLM:** large language model (Gemini here), used through an API.
- **Prompt / temperature:** the instructions + context sent to the LLM / how random its output is (low = more consistent).
- **Hallucination:** the LLM states something that isn't supported by the data.
- **Grounding:** forcing answers to rely on supplied context.
- **Embedding:** text converted to a vector of numbers where similar meanings are close.
- **Vector database:** stores embeddings and finds nearest ones.
- **RAG:** Retrieval-Augmented Generation (retrieve context, then generate an answer from it).
- **REST API / endpoint:** HTTP interface / one URL+method on it (e.g. `POST /api/v1/recommendations`).
- **Swagger / OpenAPI:** auto-generated, interactive API documentation.
- **ORM:** maps DB tables to Python objects (SQLAlchemy).
- **SBOM:** Software Bill of Materials — list of dependencies with licenses.
- **Decoupled architecture:** frontend and backend are separate apps.
- **Cold start:** free hosting spinning a sleeping app back up (slow first request).

---

## 14. Reading list (official docs, in priority order)

1. LightGBM docs — "Parameters" and the ranking / `lambdarank` sections: https://lightgbm.readthedocs.io
2. scikit-learn user guide — "Cross-validation" and "Metrics (ndcg_score)": https://scikit-learn.org
3. FastAPI tutorial (first steps, request bodies, testing): https://fastapi.tiangolo.com
4. Streamlit docs (basics, `st.dataframe`, forms): https://docs.streamlit.io
5. ChromaDB docs (collections, `add`, `query`): https://docs.trychroma.com
6. Original method papers (optional, for the references section): LambdaMART overview (Burges, 2010), LightGBM (Ke et al., 2017), RAG (Lewis et al., 2020).

---

*Next step when you're ready: Phase 1. I'll start with a short brief on synthetic data, ask you two prediction questions, then write the generator in small, explained steps.*
