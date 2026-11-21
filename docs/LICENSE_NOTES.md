# License notes

## Project license
All code, the trained model, the synthetic data, and the documentation in this repository are released under the **MIT License** (`LICENSE`), as required by the Capstone guidelines (open source, commercial-friendly, free for Firaza to use and modify).

## Dependency audit
The full Software Bill of Materials (every installed package with its license and URL) is in [`SBOM.md`](SBOM.md), generated with `pip-licenses`.

The direct dependencies are all permissive (MIT, BSD, or Apache-2.0):

| Package | Role | License |
|---|---|---|
| lightgbm | ranking model | MIT |
| scikit-learn, scipy, numpy, pandas | data processing, metrics | BSD-3-Clause |
| fastapi, pydantic, pydantic-settings, sqlalchemy | API, validation, ORM | MIT |
| uvicorn | API server | BSD-3-Clause |
| pg8000 | PostgreSQL driver (chosen instead of LGPL psycopg2) | BSD-3-Clause |
| chromadb | vector database | Apache-2.0 |
| google-genai | Gemini API client | Apache-2.0 |
| streamlit | web UI | Apache-2.0 |
| plotly | charts | MIT |
| requests | HTTP client | Apache-2.0 |
| python-dotenv | local env loading | BSD-3-Clause |
| faker, matplotlib, pip-licenses (offline tooling only) | data generation, charts, audit | MIT / PSF-based / MIT |

No GPL, AGPL, LGPL, or EPL package is installed.

## Flagged indirect dependencies (MPL-2.0)
The guidelines list MPL among licenses to avoid. Three **indirect** dependencies use it:

| Package | Pulled in by | Why it cannot be removed | Notes |
|---|---|---|---|
| `certifi` (MPL-2.0) | `requests`, `httpx` (used by the Gemini SDK) | It supplies the TLS root certificates every HTTPS client in Python uses | Used unmodified |
| `orjson` (MPL-2.0 AND (Apache-2.0 OR MIT)) | `chromadb` | Required by ChromaDB | Used unmodified |
| `tqdm` (MPL-2.0 AND MIT) | `chromadb` | Required by ChromaDB | Used unmodified |

MPL-2.0 is a *file-level* copyleft: obligations apply only to modified MPL-licensed files. This project does not modify, copy, or vendor any of these files; it installs them from PyPI as-is. It therefore places no obligation on the project's own code, which is MIT and open source in any case. We report them here for transparency and to confirm with the Dicoding team (db@student.devacademy.id) whether this is acceptable.

## Third-party services
- **Gemini API (Google AI Studio, free tier)** for embeddings and text generation. The API key is stored only in environment variables / platform secrets, never in the repository. Google's API terms do not claim ownership of the application or its outputs, so Firaza can keep using the product. **Running cost:** the free tier is enough for prototype traffic (about 100 embedding requests and a limited number of generation requests per minute). If Firaza needs higher volume, a paid Gemini plan would be needed. This would require Dicoding's approval during the bootcamp and is Firaza's choice after it.
- **Neon (Postgres) and Streamlit Community Cloud** free tiers for hosting. Both have paid tiers if usage grows.

## Data
All data is synthetic and self-generated (`docs/DATA_CARD.md`). No personal data and no confidential Firaza data are included.
