"""Generation step of RAG: call Gemini, trying the configured models in order."""
import logging

from google.genai import types

from app.config import settings
from app.rag.embeddings import EmbeddingUnavailable, client

log = logging.getLogger("firaza.llm")


class LLMUnavailable(Exception):
    pass


def generate(prompt: str, system: str) -> tuple[str, str]:
    """Return (text, model_used). Raises LLMUnavailable if no model answers."""
    try:
        c = client()
    except EmbeddingUnavailable as exc:
        raise LLMUnavailable(str(exc)) from exc
    errors = []
    for model in settings.gen_models:
        try:
            res = c.models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system, temperature=0.2,
                                                   max_output_tokens=400))
            text = (res.text or "").strip()
            if text:
                return text, model
            errors.append(f"{model}: empty response")
        except Exception as exc:  # overloaded, timeout, quota...
            errors.append(f"{model}: {str(exc)[:120]}")
            log.warning("LLM call failed for %s: %s", model, exc)
    raise LLMUnavailable("; ".join(errors))
