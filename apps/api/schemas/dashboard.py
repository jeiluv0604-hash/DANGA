# -*- coding: utf-8 -*-
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from apps.api.schemas.alerts import AlertSchema

class DashboardKPISchema(BaseModel):
    sales: Optional[float] = None
    guests: Optional[int] = None
    avg_check: Optional[float] = None
    labor_cost: Optional[float] = None
    labor_ratio: Optional[float] = None
    food_cost: Optional[float] = None
    food_cost_ratio: Optional[float] = None
    contribution: Optional[float] = None
    contribution_ratio: Optional[float] = None
    inventory_variance_kg: Optional[float] = None
    waste_ratio: Optional[float] = None
    rating: Optional[float] = None
    complaints: Optional[int] = None

class KPICoverageItem(BaseModel):
    available_days: int
    total_days: int

class DailyDashboardResponse(BaseModel):
    date: str
    dataset_type: str = "SYNTHETIC"
    data_status: str = "OK"
    blocked: bool = False
    ai_eligible: bool = True
    kpis: DashboardKPISchema
    kpi_status: Optional[Dict[str, str]] = None
    alerts: List[AlertSchema] = []
    evidence_ids: List[str] = []

class DashboardSummaryResponse(BaseModel):
    start_date: str
    end_date: str
    dataset_type: str = "SYNTHETIC"
    total_days: int
    data_complete_days: int
    data_incomplete_days: int
    total_sales: float
    average_daily_sales: float
    average_labor_ratio: Optional[float]
    average_food_cost_ratio: Optional[float]
    total_contribution: float
    average_contribution_ratio: Optional[float]
    critical_alert_count: int
    high_alert_count: int
    medium_alert_count: int
    coverage: Dict[str, KPICoverageItem]
