# -*- coding: utf-8 -*-
import hashlib
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from apps.api.dependencies import get_db
from apps.api.models.evidence import EvidenceIndex
from apps.api.schemas.evidence import EvidenceIndexResponse, EvidenceVerifyResponse

router = APIRouter(prefix="/api/v1/evidence", tags=["Evidence"])

def verify_evidence_integrity(db: Session, evidence_id: str):
    ev = db.query(EvidenceIndex).filter(EvidenceIndex.evidence_id == evidence_id).first()
    if not ev:
        return None

    file_path = ev.file_path
    if not os.path.exists(file_path):
        return {
            "evidence_id": evidence_id,
            "exists": False,
            "stored_sha256": ev.file_sha256,
            "actual_sha256": None,
            "dataset_sha256": ev.dataset_sha256,
            "integrity": "MISSING_FILE"
        }

    with open(file_path, "rb") as f:
        actual_bytes = f.read()
    actual_sha256 = hashlib.sha256(actual_bytes).hexdigest()

    integrity = "VALID" if actual_sha256 == ev.file_sha256 else "INVALID"
    return {
        "evidence_id": evidence_id,
        "exists": True,
        "stored_sha256": ev.file_sha256,
        "actual_sha256": actual_sha256,
        "dataset_sha256": ev.dataset_sha256,
        "integrity": integrity
    }

@router.get("/{evidence_id}", response_model=EvidenceIndexResponse)
def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    ev = db.query(EvidenceIndex).filter(EvidenceIndex.evidence_id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail=f"Evidence not found: {evidence_id}")
    return ev

@router.get("/{evidence_id}/verify", response_model=EvidenceVerifyResponse)
def verify_evidence(evidence_id: str, db: Session = Depends(get_db)):
    result = verify_evidence_integrity(db, evidence_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Evidence not found: {evidence_id}")
    return result
