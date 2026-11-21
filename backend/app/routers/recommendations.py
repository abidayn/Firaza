"""Inference API: rank vendors for a request, and explain the ranking (RAG)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas, services
from app.db import get_db
from app.rag.explain import explain
from app.rag.kb import rebuild_kb
from app.rag.vector_store import get_store

router = APIRouter(tags=["Recommendations"])


@router.post("/recommendations", response_model=schemas.RecommendationOut, status_code=201,
             summary="Rank vendors for a procurement need (LightGBM ranking model)")
def create_recommendation(body: schemas.RecommendationIn, db: Session = Depends(get_db)):
    return services.recommend(db, **body.model_dump())


@router.get("/recommendations/{request_id}", response_model=schemas.RecommendationOut,
            summary="Get a saved recommendation")
def read_recommendation(request_id: int, db: Session = Depends(get_db)):
    return services.get_recommendation(db, request_id)


@router.post("/recommendations/{request_id}/explanation", response_model=schemas.ExplanationOut,
             summary="Explain a recommendation in Indonesian (RAG: retrieval + Gemini, with fallback)")
def explain_recommendation(request_id: int, db: Session = Depends(get_db)):
    return explain(db, services.get_recommendation(db, request_id))


@router.get("/recommendations", summary="Recent requests")
def list_recent(limit: int = 10, db: Session = Depends(get_db)):
    return services.recent_requests(db, limit)


kb_router = APIRouter(prefix="/kb", tags=["Knowledge base"])


@kb_router.post("/rebuild", summary="Re-embed all knowledge-base documents from the database")
def rebuild(db: Session = Depends(get_db)):
    return {"documents": rebuild_kb(db), "vector_store": get_store().backend_name}


@kb_router.get("/status", summary="Knowledge-base size and vector store in use")
def status():
    store = get_store()
    return {"documents": store.count(), "vector_store": store.backend_name}
