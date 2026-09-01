# -*- coding: utf-8 -*-
import os
from pydantic import BaseModel


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///data/damga_ops.db")
    # Some hosts (e.g. Render) hand out legacy `postgres://` URLs that SQLAlchemy 2.x rejects.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


class Settings(BaseModel):
    APP_NAME: str = "DAMGA-OPS API"
    APP_VERSION: str = "6.0.0-prototype"
    DATABASE_URL: str = _database_url()
    SYNTHETIC_DATASET_PATH: str = os.getenv("SYNTHETIC_DATASET_PATH", "data/synthetic/damga_dataset.json")
    DEFAULT_DATASET_TYPE: str = "SYNTHETIC"

settings = Settings()
