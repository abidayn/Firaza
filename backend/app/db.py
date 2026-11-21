"""Database engine and sessions (SQLite locally, Neon Postgres in production)."""
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import BACKEND_DIR, settings


class Base(DeclarativeBase):
    pass


def normalize_url(url: str) -> tuple[str, dict]:
    """Turn a provider URL into a SQLAlchemy URL + driver arguments.

    Neon gives `postgresql://...?sslmode=require&channel_binding=require`. We use the
    pg8000 driver (BSD license; psycopg2 is LGPL), which does not accept `sslmode`,
    so those params are removed and TLS is switched on with `ssl_context=True`.
    Relative SQLite paths are anchored to backend/ so every entry point shares one file.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+pg8000://" + url[len("postgresql://"):]
    if url.startswith("postgresql+pg8000://"):
        parts = urlsplit(url)
        query = [(k, v) for k, v in parse_qsl(parts.query) if k not in ("sslmode", "channel_binding")]
        return urlunsplit(parts._replace(query=urlencode(query))), {"ssl_context": True}
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////") and ":memory:" not in url:
        rel = url[len("sqlite:///"):]
        path = Path(rel)
        if not path.is_absolute():
            path = (BACKEND_DIR / rel).resolve()
        return f"sqlite:///{path.as_posix()}", {"check_same_thread": False}
    return url, {"check_same_thread": False} if url.startswith("sqlite") else {}


def make_engine(url: str):
    sa_url, connect_args = normalize_url(url)
    return create_engine(sa_url, connect_args=connect_args, pool_pre_ping=True)


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
