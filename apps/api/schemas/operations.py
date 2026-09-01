# -*- coding: utf-8 -*-
from typing import Optional
from pydantic import BaseModel

class DailyOperationSchema(BaseModel):
    business_date: str
    sales: Optional[float]
    guests: Optional[int]
    labor_cost: Optional[float]
    food_cost: Optional[float]
    incoming_kg: Optional[float]
    sold_kg: Optional[float]
    service_kg: Optional[float]
    waste_kg: Optional[float]
    actual_end_kg: Optional[float]
    theory_end_kg: Optional[float]
    rating: Optional[float]
    review_count: Optional[int]
    complaints: Optional[int]
    dataset_type: str
    ingestion_id: str

    class Config:
        from_attributes = True
