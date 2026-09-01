# -*- coding: utf-8 -*-
from typing import Optional, List
from sqlalchemy.orm import Session
from apps.api.models.ingestion import IngestionRun

class IngestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_sha256(self, sha256_hash: str) -> Optional[IngestionRun]:
        return self.db.query(IngestionRun).filter(IngestionRun.source_sha256 == sha256_hash, IngestionRun.status == "COMPLETED").first()

    def create(self, run: IngestionRun) -> IngestionRun:
        self.db.add(run)
        self.db.flush()
        return run

    def list_runs(self, limit: int = 50) -> List[IngestionRun]:
        return self.db.query(IngestionRun).order_by(IngestionRun.id.desc()).limit(limit).all()
