# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from apps.api.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(64), unique=True, index=True, nullable=False)
    business_date = Column(String(10), index=True, nullable=False)
    rule_id = Column(String(32), index=True, nullable=False)
    severity = Column(String(16), index=True, nullable=False)
    status = Column(String(32), default="ALERT", nullable=False)
    actual_value = Column(String(255), nullable=True)
    threshold_value = Column(String(255), nullable=True)
    comparison = Column(String(255), nullable=True)
    message_code = Column(String(64), nullable=True)

    dataset_type = Column(String(32), default="SYNTHETIC", nullable=False)
    verification_status = Column(String(32), default="UNVERIFIED", nullable=False)
    ingestion_id = Column(String(64), index=True, nullable=False)
    evidence_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class PeriodAlert(Base):
    __tablename__ = "period_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(64), unique=True, index=True, nullable=False)
    rule_id = Column(String(32), index=True, nullable=False)
    severity = Column(String(16), index=True, nullable=False)
    baseline_start = Column(String(10), nullable=True)
    baseline_end = Column(String(10), nullable=True)
    target_start = Column(String(10), nullable=False)
    target_end = Column(String(10), nullable=False)
    metric_name = Column(String(64), nullable=True)
    baseline_value = Column(Float, nullable=True)
    target_value = Column(Float, nullable=True)
    comparison = Column(String(255), nullable=True)

    dataset_type = Column(String(32), default="SYNTHETIC", nullable=False)
    verification_status = Column(String(32), default="UNVERIFIED", nullable=False)
    ingestion_id = Column(String(64), index=True, nullable=False)
    evidence_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
