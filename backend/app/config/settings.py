from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "NeuralShift Legal AI API")
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")

    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "neuralshift")
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_secret_in_production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

    _backend_root = Path(__file__).resolve().parents[2]
    CASEFILES_ROOT_DIR: str = os.getenv(
        "CASEFILES_ROOT_DIR",
        str(_backend_root / "storage" / "casefiles"),
    )

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
