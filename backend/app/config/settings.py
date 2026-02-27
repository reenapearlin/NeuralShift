from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv

_backend_root = Path(__file__).resolve().parents[2]
_project_root = _backend_root.parent
load_dotenv(_project_root / ".env")


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "NeuralShift Legal AI API")
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_secret_in_production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

    CASEFILES_ROOT_DIR: str = os.getenv(
        "CASEFILES_ROOT_DIR",
        str(_backend_root / "storage" / "casefiles"),
    )
    PRECEDENT_SCRAPER_BASE_URL: str = os.getenv(
        "PRECEDENT_SCRAPER_BASE_URL",
        "https://indiankanoon.org/search/",
    )
    PRECEDENT_SCRAPER_USER_AGENT: str = os.getenv(
        "PRECEDENT_SCRAPER_USER_AGENT",
        "NeuralShiftLegalBot/1.0 (+https://neuralshift.local)",
    )
    PRECEDENT_SCRAPER_MAX_RESULTS: int = int(os.getenv("PRECEDENT_SCRAPER_MAX_RESULTS", "10"))
    PRECEDENT_SCRAPER_TIMEOUT: int = int(os.getenv("PRECEDENT_SCRAPER_TIMEOUT", "20"))
    PRECEDENT_SCRAPER_DELAY_SECONDS: float = float(
        os.getenv("PRECEDENT_SCRAPER_DELAY_SECONDS", "1.0")
    )
    PRECEDENT_SCRAPER_MAX_TEXT_CHARS: int = int(
        os.getenv("PRECEDENT_SCRAPER_MAX_TEXT_CHARS", "20000")
    )
    PRECEDENT_SEARCH_TOP_N: int = int(os.getenv("PRECEDENT_SEARCH_TOP_N", "5"))
    PRECEDENT_SNIPPET_CHARS: int = int(os.getenv("PRECEDENT_SNIPPET_CHARS", "300"))
    PRECEDENT_VIEW_CACHE_SECONDS: int = int(
        os.getenv("PRECEDENT_VIEW_CACHE_SECONDS", "900")
    )
    PRECEDENT_VIEW_MAX_CONTEXT_CHARS: int = int(
        os.getenv("PRECEDENT_VIEW_MAX_CONTEXT_CHARS", "4500")
    )

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        if not self.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is missing. Set it in your root .env file "
                "(example: postgresql+psycopg2://postgres:<password>@localhost:5434/neuralshift)."
            )
        return self.DATABASE_URL


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
