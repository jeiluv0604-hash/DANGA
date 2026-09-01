# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from apps.api.database import Base

class EvidenceIndex(Base):
    __tablename__ = "evidence_index"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String(64), unique=True, index=True, nullable=False)
    evidence_type = Column(String(32), nullable=False)
    business_date = Column(String(10), nullable=True)
    rule_id = Column(String(32), nullable=True)
    file_path = Column(String(255), nullable=False)
    file_sha256 = Column(String(64), nullable=False)
    dataset_sha256 = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
