# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from apps.api.dependencies import get_db
from apps.api.repositories.alerts_repository import AlertsRepository
from apps.api.schemas.alerts import AlertSchema, PeriodAlertSchema

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertSchema])
def list_alerts(start_date: Optional[str] = Query(None),
                end_date: Optional[str] = Query(None),
                severity: Optional[str] = Query(None),
                rule_id: Optional[str] = Query(None),
                db: Session = Depends(get_db)):
    if severity and severity.upper() not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "NORMAL"):
        raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    repo = AlertsRepository(db)
    return repo.list_alerts(start_date=start_date, end_date=end_date, severity=severity, rule_id=rule_id)

@router.get("/periods", response_model=List[PeriodAlertSchema])
def list_period_alerts(db: Session = Depends(get_db)):
    repo = AlertsRepository(db)
    return repo.list_period_alerts()

@router.get("/{date}", response_model=List[AlertSchema])
def get_alerts_by_date(date: str, db: Session = Depends(get_db)):
    repo = AlertsRepository(db)
    return repo.get_by_date(date)
