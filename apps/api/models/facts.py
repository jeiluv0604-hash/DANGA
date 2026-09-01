# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime
from apps.api.database import Base

class DailyFact(Base):
    __tablename__ = "daily_facts"

    id = Column(Integer, primary_key=True, index=True)
    business_date = Column(String(10), index=True, nullable=False)
    
    sales = Column(Float, nullable=True)
    guests = Column(Integer, nullable=True)
    avg_check = Column(Float, nullable=True)

    labor_cost = Column(Float, nullable=True)
    labor_ratio = Column(Float, nullable=True)

    food_cost = Column(Float, nullable=True)
    food_cost_ratio = Column(Float, nullable=True)

    incoming_kg = Column(Float, nullable=True)
    sold_kg = Column(Float, nullable=True)
    service_kg = Column(Float, nullable=True)
    waste_kg = Column(Float, nullable=True)
    waste_ratio = Column(Float, nullable=True)

    theory_end_kg = Column(Float, nullable=True)
    actual_end_kg = Column(Float, nullable=True)
    variance_kg = Column(Float, nullable=True)

    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    complaints = Column(Integer, nullable=True)

    contribution = Column(Float, nullable=True)
    contribution_ratio = Column(Float, nullable=True)

    data_status = Column(String(32), default="OK", nullable=False)
    dataset_type = Column(String(32), default="SYNTHETIC", nullable=False)
    verification_status = Column(String(32), default="UNVERIFIED", nullable=False)
    ingestion_id = Column(String(64), index=True, nullable=False)
    facts_version = Column(String(32), default="1.0.0", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
