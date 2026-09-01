# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from apps.api.dependencies import get_db
from apps.api.repositories.facts_repository import FactsRepository
from apps.api.schemas.facts import DailyFactSchema

router = APIRouter(prefix="/api/v1/facts", tags=["Facts"])

@router.get("", response_model=List[DailyFactSchema])
def list_facts(start_date: Optional[str] = Query(None),
               end_date: Optional[str] = Query(None),
               db: Session = Depends(get_db)):
    repo = FactsRepository(db)
    return repo.list_facts(start_date=start_date, end_date=end_date)

@router.get("/{date}", response_model=DailyFactSchema)
def get_facts_by_date(date: str, db: Session = Depends(get_db)):
    repo = FactsRepository(db)
    fact = repo.get_by_date(date)
    if not fact:
        raise HTTPException(status_code=404, detail=f"Facts not found for date: {date}")
    return fact
