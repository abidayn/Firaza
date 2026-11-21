"""Text -> vector, using the Gemini embedding API."""
import hashlib
import json
import time
from functools import lru_cache

from google import genai
from google.genai import types

from app.config import settings

BATCH = 50
CACHE_FILE = settings.kb_dir / "embeddings_cache.json"


class EmbeddingUnavailable(Exception):
    pass


@lru_cache(maxsize=1)
def client() -> genai.Client:
    if not settings.gemini_api_key:
        raise EmbeddingUnavailable("GEMINI_API_KEY is not set")
    return genai.Client(api_key=settings.gemini_api_key,
                        http_options=types.HttpOptions(timeout=settings.llm_timeout_s * 1000))


def _embed(texts: list[str], task_type: str) -> list[list[float]]:
    out: list[list[float]] = []
    for i in range(0, len(texts), BATCH):
        batch = texts[i:i + BATCH]
        for attempt in range(3):
            try:
                # one Content per text: newer models merge a plain list of strings into ONE embedding
                res = client().models.embed_content(
                    model=settings.gemini_embed_model,
                    contents=[types.Content(parts=[types.Part(text=t)]) for t in batch],
                    config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=settings.embed_dim))
                if len(res.embeddings) != len(batch):
                    raise EmbeddingUnavailable(f"expected {len(batch)} embeddings, got {len(res.embeddings)}")
                out.extend(e.values for e in res.embeddings)
                break
            except EmbeddingUnavailable:
                raise
            except Exception as exc:  # rate limit / transient error: back off and retry
                if attempt == 2:
                    raise EmbeddingUnavailable(str(exc)) from exc
                time.sleep(2 ** attempt)
    return out


def _key(text: str, task_type: str) -> str:
    raw = f"{settings.gemini_embed_model}|{settings.embed_dim}|{task_type}|{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_cache() -> dict:
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_cache(cache: dict) -> None:
    try:
        tmp = CACHE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache), encoding="utf-8")
        tmp.replace(CACHE_FILE)
    except OSError:
        pass  # read-only disk: keep working without persisting


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed knowledge-base documents, reusing cached vectors for unchanged text.

    The free tier allows ~100 embedding requests per minute; without the cache every
    restart would re-embed the whole knowledge base.
    """
    cache = _load_cache()
    keys = [_key(t, "RETRIEVAL_DOCUMENT") for t in texts]
    missing = [(k, t) for k, t in zip(keys, texts) if k not in cache]
    if missing:
        vectors = _embed([t for _, t in missing], "RETRIEVAL_DOCUMENT")
        for (k, _), v in zip(missing, vectors):
            cache[k] = [round(float(x), 6) for x in v]
        _save_cache(cache)
    return [cache[k] for k in keys]


@lru_cache(maxsize=256)
def _embed_query_cached(text: str) -> tuple[float, ...]:
    return tuple(_embed([text], "RETRIEVAL_QUERY")[0])


def embed_query(text: str) -> list[float]:
    return list(_embed_query_cached(text))
