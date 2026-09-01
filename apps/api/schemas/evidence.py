# -*- coding: utf-8 -*-
import datetime
from typing import Optional
from pydantic import BaseModel

class EvidenceIndexResponse(BaseModel):
    evidence_id: str
    evidence_type: str
    business_date: Optional[str] = None
    rule_id: Optional[str] = None
    file_path: str
    file_sha256: str
    dataset_sha256: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class EvidenceVerifyResponse(BaseModel):
    evidence_id: str
    exists: bool
    stored_sha256: Optional[str] = None
    actual_sha256: Optional[str] = None
    dataset_sha256: Optional[str] = None
    integrity: str # "VALID", "INVALID", "MISSING_FILE"
