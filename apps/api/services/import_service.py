# -*- coding: utf-8 -*-
import hashlib
import json
import os
import uuid
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from apps.api.repositories.imports_repository import ImportsRepository
from apps.api.schemas.imports import (
    ProfileResponse,
    MappingSuggestResponse,
    MappingSuggestItemSchema,
    ConfirmMappingRequest,
    MappingManifestResponse,
    ValidateImportResponse,
    ShadowIngestResponse
)
from domains.adapters.csv_adapter import GenericCSVAdapter
from domains.adapters.xlsx_adapter import GenericXLSXAdapter
from domains.adapters.profiling import SourceProfiler
from domains.adapters.mapping import MappingEngine
from domains.adapters.schemas import MappingManifest, RealDataQualityReport
from domains.adapters.reconciliation import ReconciliationEngine
from domains.adapters.shadow import ShadowProcessor
from domains.adapters.privacy import SensitiveColumnDetector

class ImportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ImportsRepository(db)
        self.csv_adapter = GenericCSVAdapter()
        self.xlsx_adapter = GenericXLSXAdapter()

    def profile_file(self, file_path: str, sheet_name: Optional[str] = None) -> ProfileResponse:
        dp = SourceProfiler.profile_file(file_path, sheet_name=sheet_name)
        return ProfileResponse(
            filename=dp.filename,
            file_sha256=dp.file_sha256,
            file_size_bytes=dp.file_size_bytes,
            sheet_names=dp.sheet_names,
            row_count=dp.row_count,
            column_names=dp.column_names,
            inferred_types=dp.inferred_types,
            null_counts=dp.null_counts,
            duplicate_count=dp.duplicate_count,
            min_date=dp.min_date,
            max_date=dp.max_date,
            sample_values_masked=dp.sample_values_masked,
            sensitive_columns_detected=dp.sensitive_columns_detected
        )

    def suggest_mapping(self, source_type: str, columns: List[str]) -> MappingSuggestResponse:
        suggestions = MappingEngine.suggest_mapping(source_type, columns)
        return MappingSuggestResponse(
            source_type=source_type.upper(),
            suggestions=[
                MappingSuggestItemSchema(
                    source_column=s.source_column,
                    suggested_canonical_field=s.suggested_canonical_field,
                    confidence=s.confidence,
                    status=s.status
                )
                for s in suggestions
            ]
        )

    def confirm_mapping(self, req: ConfirmMappingRequest) -> MappingManifestResponse:
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        manifest_data = {
            "mapping_id": req.mapping_id,
            "source_type": req.source_type.upper(),
            "mapping_version": req.mapping_version,
            "status": "CONFIRMED",
            "column_mapping_json": json.dumps(req.column_mappings, ensure_ascii=False),
            "transform_rules_json": json.dumps({}, ensure_ascii=False),
            "confirmed_by": req.reviewer_name or "ADMIN",
            "confirmed_at": datetime.datetime.now(datetime.timezone.utc)
        }
        saved = self.repo.save_mapping_manifest(manifest_data)
        return MappingManifestResponse(
            mapping_id=saved.mapping_id,
            source_type=saved.source_type,
            mapping_version=saved.mapping_version,
            status=saved.status,
            column_mappings=json.loads(saved.column_mapping_json),
            created_at=saved.created_at.isoformat() if saved.created_at else now_str
        )

    def validate_file(
        self,
        file_path: str,
        source_type: str,
        mapping_id: Optional[str] = None,
        column_mappings: Optional[Dict[str, str]] = None,
        sheet_name: Optional[str] = None
    ) -> ValidateImportResponse:
        adapter = self.xlsx_adapter if file_path.lower().endswith((".xlsx", ".xls")) else self.csv_adapter
        col_map = column_mappings or {}
        if not col_map and mapping_id:
            m = self.repo.get_mapping_manifest(mapping_id)
            if m:
                col_map = json.loads(m.column_mapping_json)

        manifest = MappingManifest(
            mapping_id=mapping_id or f"MAP-{source_type}-ADHOC",
            source_type=source_type.upper(),
            mapping_version="1.0.0",
            status="CONFIRMED",
            column_mappings=col_map
        )

        res = adapter.map_to_canonical(file_path, manifest, sheet_name=sheet_name)
        dp = SourceProfiler.profile_file(file_path, sheet_name=sheet_name)
        
        if dp.sensitive_columns_detected:
            readiness = "BLOCKED"
        elif res.rows_quarantined > (res.rows_received * 0.1):
            readiness = "REVIEW_REQUIRED"
        else:
            readiness = "SHADOW_READY"

        return ValidateImportResponse(
            source_type=res.source_type,
            source_system=res.source_system,
            rows_received=res.rows_received,
            rows_mapped=res.rows_mapped,
            rows_quarantined=res.rows_quarantined,
            mapping_version=res.mapping_version,
            readiness=readiness,
            quarantine_preview=[
                {
                    "source_row": q.source_row,
                    "reason": q.reason,
                    "field": q.field_name,
                    "preview": q.safe_value_preview
                }
                for q in res.quarantine_records[:5]
            ]
        )

    def ingest_shadow(
        self,
        file_path: str,
        source_type: str,
        mapping_id: Optional[str] = None,
        column_mappings: Optional[Dict[str, str]] = None,
        sheet_name: Optional[str] = None,
        force_reprocess: bool = False
    ) -> ShadowIngestResponse:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        sha256 = hashlib.sha256(file_bytes).hexdigest()

        # Idempotency check
        existing = self.repo.get_import_by_sha256(sha256)
        if existing and not force_reprocess:
            return ShadowIngestResponse(
                status="ALREADY_INGESTED",
                import_id=existing.import_id,
                source_sha256=existing.source_sha256,
                source_type=existing.source_type,
                dataset_type=existing.dataset_type,
                verification_status=existing.verification_status,
                readiness=existing.readiness,
                rows_received=existing.rows_received,
                rows_valid=existing.rows_valid,
                rows_quarantined=existing.rows_quarantined,
                reconciliation_status="MATCH"
            )

        adapter = self.xlsx_adapter if file_path.lower().endswith((".xlsx", ".xls")) else self.csv_adapter
        col_map = column_mappings or {}
        if not col_map and mapping_id:
            m = self.repo.get_mapping_manifest(mapping_id)
            if m:
                col_map = json.loads(m.column_mapping_json)

        manifest = MappingManifest(
            mapping_id=mapping_id or f"MAP-{source_type}-V1",
            source_type=source_type.upper(),
            mapping_version="1.0.0",
            status="CONFIRMED",
            column_mappings=col_map
        )

        map_res = adapter.map_to_canonical(file_path, manifest, sheet_name=sheet_name)
        dp = SourceProfiler.profile_file(file_path, sheet_name=sheet_name)

        import_id = f"IMP-{source_type.upper()}-{uuid.uuid4().hex[:8].upper()}"
        now_dt = datetime.datetime.now(datetime.timezone.utc)

        # Reconciliation
        st = source_type.upper()
        if st == "POS":
            rec_report = ReconciliationEngine.reconcile_pos_sales(import_id, map_res.canonical_records)
        elif st == "PURCHASE":
            rec_report = ReconciliationEngine.reconcile_purchases(import_id, map_res.canonical_records)
        elif st == "INVENTORY":
            rec_report = ReconciliationEngine.reconcile_inventory(import_id, map_res.canonical_records)
        else:
            rec_report = ReconciliationEngine.reconcile_pos_sales(import_id, [])

        if dp.sensitive_columns_detected:
            readiness = "BLOCKED"
        elif map_res.rows_quarantined > 0 or rec_report.overall_status in ["MINOR_MISMATCH", "MAJOR_MISMATCH"]:
            readiness = "REVIEW_REQUIRED"
        else:
            readiness = "SHADOW_READY"

        quality_report = RealDataQualityReport(
            import_id=import_id,
            rows_received=map_res.rows_received,
            rows_valid=map_res.rows_mapped,
            rows_quarantined=map_res.rows_quarantined,
            rows_duplicate=dp.duplicate_count,
            completeness_score=round(map_res.rows_mapped / map_res.rows_received, 4) if map_res.rows_received > 0 else 1.0,
            date_coverage_start=dp.min_date,
            date_coverage_end=dp.max_date,
            mapping_status="CONFIRMED",
            reconciliation_status=rec_report.overall_status,
            sensitive_columns_count=len(dp.sensitive_columns_detected),
            readiness=readiness
        )

        import_record = {
            "import_id": import_id,
            "filename": os.path.basename(file_path),
            "source_sha256": sha256,
            "source_type": st,
            "source_system": map_res.source_system,
            "mapping_id": manifest.mapping_id,
            "mapping_version": manifest.mapping_version,
            "dataset_type": "SHADOW_REAL",
            "verification_status": "RECONCILED" if rec_report.overall_status == "MATCH" else "VALIDATED",
            "readiness": readiness,
            "rows_received": map_res.rows_received,
            "rows_valid": map_res.rows_mapped,
            "rows_quarantined": map_res.rows_quarantined,
            "rows_duplicate": dp.duplicate_count,
            "rows_reconciled": map_res.rows_mapped,
            "profile_json": dp.model_dump_json(),
            "quality_report_json": quality_report.model_dump_json(),
            "reconciliation_json": rec_report.model_dump_json(),
            "started_at": now_dt,
            "completed_at": now_dt
        }
        self.repo.save_import(import_record)

        # Save Quarantine Records
        quarantine_dicts = []
        for q in map_res.quarantine_records:
            quarantine_dicts.append({
                "quarantine_id": q.quarantine_id,
                "import_id": import_id,
                "source_file": q.source_file,
                "source_row": q.source_row,
                "reason": q.reason,
                "field_name": q.field_name,
                "safe_value_preview": q.safe_value_preview,
                "created_at": now_dt
            })
        self.repo.save_quarantine_records(quarantine_dicts)

        # Save Canonical Records with lineage
        for r in map_res.canonical_records:
            r["import_id"] = import_id
            r["dataset_type"] = "SHADOW_REAL"
            r["verification_status"] = "RECONCILED"

        if st == "POS":
            self.repo.save_canonical_pos(map_res.canonical_records)
        elif st == "ATTENDANCE":
            self.repo.save_canonical_attendance(map_res.canonical_records)
        elif st == "PURCHASE":
            self.repo.save_canonical_purchase(map_res.canonical_records)
        elif st == "INVENTORY":
            self.repo.save_canonical_inventory(map_res.canonical_records)

        return ShadowIngestResponse(
            status="COMPLETED",
            import_id=import_id,
            source_sha256=sha256,
            source_type=st,
            dataset_type="SHADOW_REAL",
            verification_status="RECONCILED" if rec_report.overall_status == "MATCH" else "VALIDATED",
            readiness=readiness,
            rows_received=map_res.rows_received,
            rows_valid=map_res.rows_mapped,
            rows_quarantined=map_res.rows_quarantined,
            reconciliation_status=rec_report.overall_status
        )

