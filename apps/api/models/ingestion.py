# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from apps.api.database import Base

class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True, index=True)
    ingestion_id = Column(String(64), unique=True, index=True, nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    source_type = Column(String(32), default="JSON", nullable=False)
    source_filename = Column(String(255), nullable=False)
    source_sha256 = Column(String(64), index=True, nullable=False)
    dataset_type = Column(String(32), default="SYNTHETIC", nullable=False)
    verification_status = Column(String(32), default="UNVERIFIED", nullable=False)
    status = Column(String(32), default="IN_PROGRESS", nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
    valid_row_count = Column(Integer, default=0, nullable=False)
    blocked_row_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    code_version = Column(String(32), default="2.0.0-phase2", nullable=False)
