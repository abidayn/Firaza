"""Check the Gemini API key and list usable model ids.

Run from the repo root:  .venv/Scripts/python backend/scripts/check_gemini.py
Never prints the key itself.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

key = os.getenv("GEMINI_API_KEY", "")
if not key:
    sys.exit("GEMINI_API_KEY is empty in .env")
print(f"key present (length {len(key)})")

client = genai.Client(api_key=key)

gen_models, embed_models = [], []
for m in client.models.list():
    actions = getattr(m, "supported_actions", None) or []
    if "generateContent" in actions:
        gen_models.append(m.name)
    if "embedContent" in actions:
        embed_models.append(m.name)

print("\n# generation models")
for n in gen_models:
    print(" ", n)
print("\n# embedding models")
for n in embed_models:
    print(" ", n)

gen = os.getenv("GEMINI_GEN_MODEL") or next((n for n in gen_models if "flash" in n and "lite" not in n), gen_models[0])
emb = os.getenv("GEMINI_EMBED_MODEL") or next((n for n in embed_models if "embedding" in n), embed_models[0])

reply = client.models.generate_content(model=gen, contents="Jawab satu kata: halo")
print(f"\ngeneration test with {gen}: {reply.text.strip()!r}")

vec = client.models.embed_content(model=emb, contents=["uji embedding"]).embeddings[0].values
print(f"embedding test with {emb}: length {len(vec)}")
