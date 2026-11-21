"""Shared helpers for the Streamlit pages.

The UI calls the same service layer as the REST API (backend/app/services.py),
so both entry points behave identically.
"""
import sys
from contextlib import contextmanager
from pathlib import Path

import streamlit as st

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app import models, services  # noqa: E402
from app.config import settings  # noqa: E402
from app.core.ranker import model_loaded  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.rag.vector_store import get_store  # noqa: E402

__all__ = ["models", "services", "settings", "session", "setup", "rp", "pct", "status"]


@st.cache_resource(show_spinner="Menyiapkan database dan model...")
def _bootstrap() -> dict:
    services.init_db()
    with SessionLocal() as db:
        seeded = services.seed_if_empty(db)
    return {"seeded": seeded, "model_loaded": model_loaded()}


@contextmanager
def session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup(title: str) -> None:
    st.set_page_config(page_title=f"{title} | Firaza Procurement", page_icon="📦", layout="wide")
    _bootstrap()


def status() -> dict:
    return {"model_loaded": model_loaded(), "vector_store": get_store().backend_name,
            "llm_configured": bool(settings.gemini_api_key)}


def rp(x: float) -> str:
    return "Rp " + f"{x:,.0f}".replace(",", ".")


def pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def show_error(exc: Exception) -> None:
    if isinstance(exc, (services.NotFound, services.Conflict, services.Invalid)):
        st.error(str(exc))
    else:
        st.error("Terjadi kesalahan. Coba lagi, atau periksa koneksi database.")
