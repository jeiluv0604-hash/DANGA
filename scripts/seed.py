# -*- coding: utf-8 -*-
"""Idempotent database seed for deployment.

Runs the synthetic Golden Dataset through the deterministic ingestion pipeline so
a freshly-provisioned environment has `daily_facts` / `alerts` populated. Safe to
run on every container boot: ingestion is keyed by the source file SHA-256 and
short-circuits with ALREADY_INGESTED when the dataset is unchanged.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.api.config import settings
from apps.api.database import SessionLocal
from apps.api.services.ingestion_service import IngestionService


def main() -> None:
    dataset_path = os.getenv("SYNTHETIC_DATASET_PATH", settings.SYNTHETIC_DATASET_PATH)
    if not os.path.exists(dataset_path):
        raise SystemExit(f"Synthetic dataset not found: {dataset_path}")

    db = SessionLocal()
    try:
        result = IngestionService(db).ingest_synthetic_dataset(dataset_path, dataset_type="SYNTHETIC")
    finally:
        db.close()

    print(
        "seed:",
        result.get("status"),
        "ingestion_id=" + str(result.get("ingestion_id")),
        "rows=" + str(result.get("row_count")),
        "valid=" + str(result.get("valid_row_count")),
        "blocked=" + str(result.get("blocked_row_count")),
    )


if __name__ == "__main__":
    main()
