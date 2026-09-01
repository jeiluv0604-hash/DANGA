# -*- coding: utf-8 -*-
import datetime
from typing import Optional, List
from pydantic import BaseModel

class IngestionRunResponse(BaseModel):
    ingestion_id: str
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime]
    source_type: str
    source_filename: str
    source_sha256: str
    dataset_type: str
    status: str
    row_count: int
    valid_row_count: int
    blocked_row_count: int
    error_count: int

    class Config:
        from_attributes = True

class IngestionResult(BaseModel):
    ingestion_id: str
    dataset_type: str
    status: str
    row_count: int
    valid_row_count: int
    blocked_row_count: int
    alerts_count: int
    period_alerts_count: int
    source_sha256: str
