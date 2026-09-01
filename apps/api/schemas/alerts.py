# -*- coding: utf-8 -*-
from typing import Optional
from pydantic import BaseModel

class AlertSchema(BaseModel):
    alert_id: str
    business_date: str
    rule_id: str
    severity: str
    status: str
    actual_value: Optional[str]
    threshold_value: Optional[str]
    comparison: Optional[str]
    dataset_type: str
    ingestion_id: str
    evidence_id: Optional[str]

    class Config:
        from_attributes = True

class PeriodAlertSchema(BaseModel):
    alert_id: str
    rule_id: str
    severity: str
    baseline_start: Optional[str]
    baseline_end: Optional[str]
    target_start: str
    target_end: str
    metric_name: Optional[str]
    baseline_value: Optional[float]
    target_value: Optional[float]
    comparison: Optional[str]
    dataset_type: str
    ingestion_id: str
    evidence_id: Optional[str]

    class Config:
        from_attributes = True
