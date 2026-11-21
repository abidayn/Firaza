"""App settings, read from environment variables (and .env for local runs).

On Streamlit Community Cloud / Render the same names are set as secrets / env vars.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(ROOT_DIR / ".env", BACKEND_DIR / ".env"), extra="ignore")

    database_url: str = "sqlite:///./firaza.db"
    gemini_api_key: str = ""
    # comma-separated: tried in order until one answers
    gemini_gen_model: str = "models/gemini-3.5-flash-lite,models/gemini-3.8-flash"
    gemini_embed_model: str = "models/gemini-embedding-2"
    embed_dim: int = 768
    llm_timeout_s: int = 20

    artifacts_dir: Path = BACKEND_DIR / "artifacts"
    kb_dir: Path = BACKEND_DIR / "kb"
    seed_dir: Path = ROOT_DIR / "ml" / "data"

    @property
    def gen_models(self) -> list[str]:
        return [m.strip() for m in self.gemini_gen_model.split(",") if m.strip()]


settings = Settings()
