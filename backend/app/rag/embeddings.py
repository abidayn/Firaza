"""Text -> vector, using the Gemini embedding API."""
import time
from functools import lru_cache

from google import genai
from google.genai import types

from app.config import settings

BATCH = 50


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


def embed_documents(texts: list[str]) -> list[list[float]]:
    return _embed(texts, "RETRIEVAL_DOCUMENT")


def embed_query(text: str) -> list[float]:
    return _embed([text], "RETRIEVAL_QUERY")[0]
