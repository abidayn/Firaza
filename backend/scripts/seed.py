"""Load the synthetic CSVs (ml/data) into the database.

  .venv/Scripts/python backend/scripts/seed.py                # DATABASE_URL (local SQLite by default)
  .venv/Scripts/python backend/scripts/seed.py --target prod  # PROD_DATABASE_URL (Neon)
  add --reset to wipe and reload
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

parser = argparse.ArgumentParser()
parser.add_argument("--target", choices=["local", "prod"], default="local")
parser.add_argument("--reset", action="store_true")
args = parser.parse_args()

if args.target == "prod":
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    if not os.getenv("PROD_DATABASE_URL"):
        sys.exit("PROD_DATABASE_URL is empty in .env")
    os.environ["DATABASE_URL"] = os.environ["PROD_DATABASE_URL"]

from app import services  # noqa: E402  (import after DATABASE_URL is chosen)
from app.db import SessionLocal, engine  # noqa: E402

services.init_db()
with SessionLocal() as db:
    print("database:", engine.url.render_as_string(hide_password=True).split("@")[-1])
    print(services.seed_if_empty(db, reset=args.reset))
    print("row counts:", services.counts(db))
