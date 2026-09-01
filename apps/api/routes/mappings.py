# -*- coding: utf-8 -*-
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.dependencies import get_db
from apps.api.services.import_service import ImportService
from apps.api.schemas.imports import ConfirmMappingRequest, MappingManifestResponse

router = APIRouter(prefix="/api/v1/mappings", tags=["Mapping Manifests"])

@router.post("/confirm", response_model=MappingManifestResponse)
def confirm_mapping(req: ConfirmMappingRequest, db: Session = Depends(get_db)):
    svc = ImportService(db)
    return svc.confirm_mapping(req)

@router.get("", response_model=List[MappingManifestResponse])
def list_mappings(db: Session = Depends(get_db)):
    svc = ImportService(db)
    items = svc.repo.list_mapping_manifests()
    return [
        MappingManifestResponse(
            mapping_id=m.mapping_id,
            source_type=m.source_type,
            mapping_version=m.mapping_version,
            status=m.status,
            column_mappings=json.loads(m.column_mapping_json),
            created_at=m.created_at.isoformat() if m.created_at else None
        )
        for m in items
    ]

@router.get("/{mapping_id}", response_model=MappingManifestResponse)
def get_mapping(mapping_id: str, db: Session = Depends(get_db)):
    svc = ImportService(db)
    m = svc.repo.get_mapping_manifest(mapping_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Mapping {mapping_id} not found")
    return MappingManifestResponse(
        mapping_id=m.mapping_id,
        source_type=m.source_type,
        mapping_version=m.mapping_version,
        status=m.status,
        column_mappings=json.loads(m.column_mapping_json),
        created_at=m.created_at.isoformat() if m.created_at else None
    )

