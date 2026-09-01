# -*- coding: utf-8 -*-
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from apps.api.models.imports import SourceImportModel, QuarantineRecordModel, MappingManifestModel
from apps.api.models.canonical import (
    CanonicalPOSModel,
    CanonicalAttendanceModel,
    CanonicalPurchaseModel,
    CanonicalInventoryModel
)

class ImportsRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_import(self, data: Dict[str, Any]) -> SourceImportModel:
        model = SourceImportModel(**data)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_import_by_id(self, import_id: str) -> Optional[SourceImportModel]:
        return self.db.query(SourceImportModel).filter(SourceImportModel.import_id == import_id).first()

    def get_import_by_sha256(self, sha256: str) -> Optional[SourceImportModel]:
        return self.db.query(SourceImportModel).filter(SourceImportModel.source_sha256 == sha256).first()

    def list_imports(self) -> List[SourceImportModel]:
        return self.db.query(SourceImportModel).order_by(SourceImportModel.started_at.desc()).all()

    def save_quarantine_records(self, records: List[Dict[str, Any]]):
        for r in records:
            q = QuarantineRecordModel(**r)
            self.db.add(q)
        self.db.commit()

    def get_quarantine_by_import(self, import_id: str) -> List[QuarantineRecordModel]:
        return self.db.query(QuarantineRecordModel).filter(QuarantineRecordModel.import_id == import_id).all()

    def save_mapping_manifest(self, data: Dict[str, Any]) -> MappingManifestModel:
        existing = self.get_mapping_manifest(data['mapping_id'])
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        model = MappingManifestModel(**data)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_mapping_manifest(self, mapping_id: str) -> Optional[MappingManifestModel]:
        return self.db.query(MappingManifestModel).filter(MappingManifestModel.mapping_id == mapping_id).first()

    def list_mapping_manifests(self) -> List[MappingManifestModel]:
        return self.db.query(MappingManifestModel).all()

    def save_canonical_pos(self, records: List[Dict[str, Any]]):
        for r in records:
            rec = CanonicalPOSModel(**r)
            self.db.add(rec)
        self.db.commit()

    def save_canonical_attendance(self, records: List[Dict[str, Any]]):
        for r in records:
            rec = CanonicalAttendanceModel(**r)
            self.db.add(rec)
        self.db.commit()

    def save_canonical_purchase(self, records: List[Dict[str, Any]]):
        for r in records:
            rec = CanonicalPurchaseModel(**r)
            self.db.add(rec)
        self.db.commit()

    def save_canonical_inventory(self, records: List[Dict[str, Any]]):
        for r in records:
            rec = CanonicalInventoryModel(**r)
            self.db.add(rec)
        self.db.commit()
