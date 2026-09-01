# -*- coding: utf-8 -*-
import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "DAMGA-OPS API"
    APP_VERSION: str = "6.0.0-prototype"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/damga_ops.db")
    SYNTHETIC_DATASET_PATH: str = os.getenv("SYNTHETIC_DATASET_PATH", "data/synthetic/damga_dataset.json")
    DEFAULT_DATASET_TYPE: str = "SYNTHETIC"

settings = Settings()
