# -*- coding: utf-8 -*-
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from apps.api.dependencies import get_db
from apps.api.services.dashboard_service import DashboardService
from apps.api.schemas.dashboard import DailyDashboardResponse, DashboardSummaryResponse

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

@router.get("/daily/{date}", response_model=DailyDashboardResponse)
def get_daily_dashboard(date: str, db: Session = Depends(get_db)):
    service = DashboardService(db)
    dash = service.get_daily_dashboard(date)
    if not dash:
        raise HTTPException(status_code=404, detail=f"Dashboard data not found for date: {date}")
    return dash

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(start_date: Optional[str] = Query(None),
                          end_date: Optional[str] = Query(None),
                          db: Session = Depends(get_db)):
    service = DashboardService(db)
    return service.get_dashboard_summary(start_date=start_date, end_date=end_date)
