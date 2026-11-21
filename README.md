# Firaza Vendor Recommendation & Procurement Assistant

Capstone project, Dicoding Bootcamp Batch 15 (group ID DB15-I036, individual, Generative AI path).
Use case: Firaza, Use Case 3 - Vendor Recommendation & Procurement Assistant.

A decision-support web app that ranks vendors for a procurement need (a trained LightGBM ranking model)
and explains the ranking in Indonesian (RAG: Gemini embeddings + ChromaDB + Gemini generation).
All data is synthetic; results are prototype results, not claims about Firaza's real data.

> This README is a skeleton. The full version (install, run, API, licenses, citations) is written in plan.md phase P7.

## Layout
- `backend/`  FastAPI REST API, ranking inference, RAG
- `frontend/` Streamlit UI
- `ml/`       synthetic data generation, training, evaluation (offline)
- `docs/`     data card, model card, user guide, SBOM
- `plan.md`   the execution plan

## License
MIT (see `LICENSE`).
