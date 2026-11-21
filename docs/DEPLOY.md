# Deploy (only the steps that need your accounts)

The app is one Streamlit deployment (the individual GenAI track allows this) backed by a Neon Postgres database.
Total time: about 15 minutes.

## 1. Neon connection string (2 min)
1. Open https://console.neon.tech → project **sweet-dream-44689469** (the one you created) → **Connect**.
2. Copy the connection string (starts with `postgresql://`, ends with `?sslmode=require...`). Keep the default role and database.
3. Paste it into `.env` after `PROD_DATABASE_URL=` (local file only, never commit it).

Optional check from your machine (also loads the data, though the app does this itself on first start):
```bash
.venv/Scripts/python backend/scripts/seed.py --target prod
```
Expected: `{'seeded': True, 'vendors': 32, ...}`.

> Note: Neon's onboarding prompt (`npm i -g neon`, `neon init`, `neon deploy`, `npm run build`) targets JavaScript apps. This project is Python, so you only need the connection string above. The code already handles Neon's TLS settings with the `pg8000` driver.

## 2. Streamlit Community Cloud (10 min)
1. https://share.streamlit.io → sign in with GitHub (`abidayn`).
2. **Create app** → **Deploy a public app from GitHub**:
   - Repository: `abidayn/Firaza` · Branch: `main` · Main file path: `frontend/Beranda.py`
   - App URL: pick something like `firaza-vendor`.
3. **Advanced settings**:
   - Python version: **3.12**
   - Secrets (paste, replacing the placeholders with your real values):
     ```toml
     GEMINI_API_KEY = "your-key"
     GEMINI_GEN_MODEL = "models/gemini-3.5-flash-lite,models/gemini-3.8-flash"
     GEMINI_EMBED_MODEL = "models/gemini-embedding-2"
     DATABASE_URL = "postgresql://...your Neon string..."
     ```
4. **Deploy**. The first build takes a few minutes (installs LightGBM and ChromaDB).

**Done when:** the home page shows *Model ranking: Siap*, *Penjelasan AI: Gemini aktif*, *Vector store: chromadb*, and 32 vendors. Then run one recommendation and check the explanation label says *Dihasilkan Gemini*.

If the vector store shows `numpy-fallback` on the cloud, the app still works (same retrieval logic). Tell me and I will check the logs.

## 3. (Optional) FastAPI on Render
Only if you want a public URL for the REST API / Swagger docs as well.
https://render.com → New → Web Service → repo `abidayn/Firaza`:
- Root Directory `backend` · Build `pip install -r requirements.txt` · Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT` · Free instance
- Environment: `PYTHON_VERSION=3.12.7`, plus the same four variables as above.

Swagger will then be at `https://<service>.onrender.com/docs`. Locally it always works at http://localhost:8000/docs.

## 4. After deploying
Send me the app URL. I will add it to the README and the Project Brief, and run the end-to-end checks.

## Security reminder
The Gemini key was pasted in chat once. After submission, rotate it: in Google AI Studio, delete it and create a new one, then update `.env` and the Streamlit secret.
