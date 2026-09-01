# -*- coding: utf-8 -*-
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.dependencies import get_db
from apps.api.services.import_service import ImportService
from apps.api.schemas.imports import (
    ProfileRequest,
    ProfileResponse,
    MappingSuggestRequest,
    MappingSuggestResponse,
    ValidateImportRequest,
    ValidateImportResponse,
    ShadowIngestRequest,
    ShadowIngestResponse,
    SourceImportListItem,
    QuarantineItemSchema
)

router = APIRouter(prefix="/api/v1/imports", tags=["Real Data Ingestion & Adapters"])

@router.post("/profile", response_model=ProfileResponse)
def profile_file(req: ProfileRequest, db: Session = Depends(get_db)):
    svc = ImportService(db)
    return svc.profile_file(req.file_path, sheet_name=req.sheet_name)

@router.post("/map", response_model=MappingSuggestResponse)
def suggest_mapping(req: MappingSuggestRequest, db: Session = Depends(get_db)):
    svc = ImportService(db)
    return svc.suggest_mapping(req.source_type, req.columns)

@router.post("/validate", response_model=ValidateImportResponse)
def validate_import(req: ValidateImportRequest, db: Session = Depends(get_db)):
    svc = ImportService(db)
    return svc.validate_file(
        req.file_path,
        req.source_type,
        mapping_id=req.mapping_id,
        column_mappings=req.column_mappings,
        sheet_name=req.sheet_name
    )

@router.post("/ingest-shadow", response_model=ShadowIngestResponse)
def ingest_shadow(req: ShadowIngestRequest, db: Session = Depends(get_db)):
    svc = ImportService(db)
    return svc.ingest_shadow(
        req.file_path,
        req.source_type,
        mapping_id=req.mapping_id,
        column_mappings=req.column_mappings,
        sheet_name=req.sheet_name,
        force_reprocess=req.force_reprocess
    )

@router.get("", response_model=List[SourceImportListItem])
def list_imports(db: Session = Depends(get_db)):
    svc = ImportService(db)
    items = svc.repo.list_imports()
    return [
        SourceImportListItem(
            import_id=i.import_id,
            filename=i.filename,
            source_sha256=i.source_sha256,
            source_type=i.source_type,
            dataset_type=i.dataset_type,
            verification_status=i.verification_status,
            readiness=i.readiness,
            rows_received=i.rows_received,
            rows_valid=i.rows_valid,
            rows_quarantined=i.rows_quarantined,
            started_at=i.started_at.isoformat() if i.started_at else None,
            completed_at=i.completed_at.isoformat() if i.completed_at else None
        )
        for i in items
    ]

@router.get("/{import_id}")
def get_import_detail(import_id: str, db: Session = Depends(get_db)):
    svc = ImportService(db)
    imp = svc.repo.get_import_by_id(import_id)
    if not imp:
        raise HTTPException(status_code=404, detail=f"Import {import_id} not found")
    return {
        "import_id": imp.import_id,
        "filename": imp.filename,
        "source_sha256": imp.source_sha256,
        "source_type": imp.source_type,
        "dataset_type": imp.dataset_type,
        "verification_status": imp.verification_status,
        "readiness": imp.readiness,
        "rows_received": imp.rows_received,
        "rows_valid": imp.rows_valid,
        "rows_quarantined": imp.rows_quarantined,
        "profile": json.loads(imp.profile_json) if imp.profile_json else None,
        "quality_report": json.loads(imp.quality_report_json) if imp.quality_report_json else None,
        "reconciliation": json.loads(imp.reconciliation_json) if imp.reconciliation_json else None
    }

@router.get("/{import_id}/quality")
def get_import_quality_report(import_id: str, db: Session = Depends(get_db)):
    svc = ImportService(db)
    imp = svc.repo.get_import_by_id(import_id)
    if not imp:
        raise HTTPException(status_code=404, detail=f"Import {import_id} not found")
    if not imp.quality_report_json:
        raise HTTPException(status_code=404, detail="No quality report available")
    return json.loads(imp.quality_report_json)

@router.get("/{import_id}/quarantine", response_model=List[QuarantineItemSchema])
def get_import_quarantine(import_id: str, db: Session = Depends(get_db)):
    svc = ImportService(db)
    records = svc.repo.get_quarantine_by_import(import_id)
    return [
        QuarantineItemSchema(
            quarantine_id=q.quarantine_id,
            import_id=q.import_id,
            source_file=q.source_file,
            source_row=q.source_row,
            reason=q.reason,
            field_name=q.field_name,
            safe_value_preview=q.safe_value_preview,
            created_at=q.created_at.isoformat() if q.created_at else None
        )
        for q in records
    ]

@router.get("/{import_id}/reconciliation")
def get_import_reconciliation(import_id: str, db: Session = Depends(get_db)):
    svc = ImportService(db)
    imp = svc.repo.get_import_by_id(import_id)
    if not imp:
        raise HTTPException(status_code=404, detail=f"Import {import_id} not found")
    if not imp.reconciliation_json:
        raise HTTPException(status_code=404, detail="No reconciliation report available")
    return json.loads(imp.reconciliation_json)

