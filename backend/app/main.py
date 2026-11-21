"""FastAPI application: REST API for CRUD + inference. Interactive docs at /docs."""
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from app import services
from app.core.ranker import model_loaded
from app.db import SessionLocal
from app.rag.vector_store import get_store
from app.routers import crud
from app.routers.recommendations import kb_router, router as rec_router

log = logging.getLogger("firaza")


@asynccontextmanager
async def lifespan(_: FastAPI):
    services.init_db()
    with SessionLocal() as db:
        services.seed_if_empty(db)
    yield


app = FastAPI(title="Firaza Vendor Recommendation API", version="1.0",
              description="Ranks vendors for a procurement need with a trained LightGBM LambdaRank model and "
                          "explains the ranking with RAG (Gemini embeddings + vector store + Gemini).",
              lifespan=lifespan)


@app.exception_handler(services.NotFound)
async def not_found(_: Request, exc: services.NotFound):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(services.Conflict)
async def conflict(_: Request, exc: services.Conflict):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(services.Invalid)
async def invalid(_: Request, exc: services.Invalid):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unexpected(_: Request, exc: Exception):
    log.exception("unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Terjadi kesalahan di server. Silakan coba lagi."})


api = APIRouter(prefix="/api/v1")


@api.get("/health", tags=["Health"], summary="Service status")
def health():
    return {"status": "ok", "model_loaded": model_loaded(), "vector_store": get_store().backend_name}


for r in (crud.vendors, crud.materials, crud.vendor_materials, crud.transactions, rec_router, kb_router):
    api.include_router(r)
app.include_router(api)
