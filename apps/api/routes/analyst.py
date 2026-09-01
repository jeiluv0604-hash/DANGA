# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from apps.api.dependencies import get_db
from apps.api.services.analyst_service import AnalystService
from apps.api.repositories.analyst_repository import InvalidStateTransitionError
from apps.api.schemas.analyst import AnalystBriefResponse, DecisionAuditLogItem, HumanReviewActionRequest

router = APIRouter(prefix="/api/v1/analyst", tags=["AI Analyst"])

@router.post("/daily/{business_date}", response_model=AnalystBriefResponse)
def generate_daily_brief(
    business_date: str,
    regenerate: bool = Query(False, description="Force regenerate even if brief exists"),
    db: Session = Depends(get_db)
):
    service = AnalystService(db)
    return service.generate_daily_brief(business_date, regenerate=regenerate)

@router.get("/daily/{business_date}", response_model=AnalystBriefResponse)
def get_daily_brief(business_date: str, db: Session = Depends(get_db)):
    service = AnalystService(db)
    brief = service.get_daily_brief(business_date)
    if not brief:
        raise HTTPException(status_code=404, detail=f"No brief found for date {business_date}")
    return brief

@router.get("/briefs/{brief_id}", response_model=AnalystBriefResponse)
def get_brief_by_id(brief_id: str, db: Session = Depends(get_db)):
    service = AnalystService(db)
    brief = service.get_brief_by_id(brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")
    return brief

@router.post("/briefs/{brief_id}/approve", response_model=AnalystBriefResponse)
def approve_brief(brief_id: str, req: HumanReviewActionRequest, db: Session = Depends(get_db)):
    service = AnalystService(db)
    try:
        brief = service.approve_brief(brief_id, req.reviewer_role, req.comment)
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not brief:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")
    return brief

@router.post("/briefs/{brief_id}/reject", response_model=AnalystBriefResponse)
def reject_brief(brief_id: str, req: HumanReviewActionRequest, db: Session = Depends(get_db)):
    service = AnalystService(db)
    try:
        brief = service.reject_brief(brief_id, req.reviewer_role, req.comment)
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not brief:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")
    return brief

@router.get("/briefs/{brief_id}/audit", response_model=List[DecisionAuditLogItem])
def get_brief_audit_trail(brief_id: str, db: Session = Depends(get_db)):
    service = AnalystService(db)
    return service.get_audit_trail(brief_id)

@router.get("/briefs/{brief_id}/audit/verify")
def verify_brief_audit_trail(brief_id: str, db: Session = Depends(get_db)):
    service = AnalystService(db)
    return service.verify_audit_trail(brief_id)

