# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from apps.api.dependencies import get_db
from apps.api.repositories.operations_repository import OperationsRepository
from apps.api.schemas.operations import DailyOperationSchema

router = APIRouter(prefix="/api/v1/operations", tags=["Operations"])

@router.get("", response_model=List[DailyOperationSchema])
def list_operations(start_date: Optional[str] = Query(None),
                    end_date: Optional[str] = Query(None),
                    db: Session = Depends(get_db)):
    repo = OperationsRepository(db)
    return repo.list_operations(start_date=start_date, end_date=end_date)
