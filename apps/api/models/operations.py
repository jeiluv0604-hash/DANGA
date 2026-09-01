# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime
from apps.api.database import Base

class DailyOperation(Base):
    __tablename__ = "daily_operations"

    id = Column(Integer, primary_key=True, index=True)
    business_date = Column(String(10), index=True, nullable=False)
    raw_date = Column(String(32), nullable=True)
    sales = Column(Float, nullable=True)
    guests = Column(Integer, nullable=True)
    labor_cost = Column(Float, nullable=True)
    food_cost = Column(Float, nullable=True)
    incoming_kg = Column(Float, nullable=True)
    sold_kg = Column(Float, nullable=True)
    service_kg = Column(Float, nullable=True)
    waste_kg = Column(Float, nullable=True)
    actual_end_kg = Column(Float, nullable=True)
    theory_end_kg = Column(Float, nullable=True)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    complaints = Column(Integer, nullable=True)

    dataset_type = Column(String(32), default="SYNTHETIC", nullable=False)
    verification_status = Column(String(32), default="UNVERIFIED", nullable=False)
    ingestion_id = Column(String(64), index=True, nullable=False)
    source_row = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
