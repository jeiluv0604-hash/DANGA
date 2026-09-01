# -*- coding: utf-8 -*-
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from apps.api.dependencies import get_db
from apps.api.config import settings
from apps.api.services.ingestion_service import IngestionService
from apps.api.schemas.ingestion import IngestionResult, IngestionRunResponse
from apps.api.repositories.ingestion_repository import IngestionRepository

router = APIRouter(prefix="/api/v1/ingestions", tags=["Ingestion"])

@router.post("/synthetic", response_model=IngestionResult)
def ingest_synthetic(file_path: str = Query(default=settings.SYNTHETIC_DATASET_PATH),
                    db: Session = Depends(get_db)):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    service = IngestionService(db)
    result = service.ingest_synthetic_dataset(file_path=file_path, dataset_type="SYNTHETIC")
    return result

@router.get("", response_model=List[IngestionRunResponse])
def list_ingestions(limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db)):
    repo = IngestionRepository(db)
    return repo.list_runs(limit=limit)
