# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ProfileRequest(BaseModel):
    file_path: str
    sheet_name: Optional[str] = None

class ProfileResponse(BaseModel):
    filename: str
    file_sha256: str
    file_size_bytes: int
    sheet_names: List[str] = []
    row_count: int
    column_names: List[str]
    inferred_types: Dict[str, str]
    null_counts: Dict[str, int]
    duplicate_count: int
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    sample_values_masked: Dict[str, List[Any]] = {}
    sensitive_columns_detected: List[str] = []

class MappingSuggestRequest(BaseModel):
    source_type: str
    columns: List[str]

class MappingSuggestItemSchema(BaseModel):
    source_column: str
    suggested_canonical_field: Optional[str] = None
    confidence: str
    status: str

class MappingSuggestResponse(BaseModel):
    source_type: str
    suggestions: List[MappingSuggestItemSchema]

class ConfirmMappingRequest(BaseModel):
    mapping_id: str
    source_type: str
    mapping_version: str = '1.0.0'
    column_mappings: Dict[str, str]
    reviewer_name: Optional[str] = 'ADMIN'

class MappingManifestResponse(BaseModel):
    mapping_id: str
    source_type: str
    mapping_version: str
    status: str
    column_mappings: Dict[str, str]
    created_at: Optional[str] = None

class ValidateImportRequest(BaseModel):
    file_path: str
    source_type: str
    mapping_id: Optional[str] = None
    column_mappings: Optional[Dict[str, str]] = None
    sheet_name: Optional[str] = None

class ValidateImportResponse(BaseModel):
    source_type: str
    source_system: str
    rows_received: int
    rows_mapped: int
    rows_quarantined: int
    mapping_version: str
    readiness: str
    quarantine_preview: List[Dict[str, Any]] = []

class ShadowIngestRequest(BaseModel):
    file_path: str
    source_type: str
    mapping_id: Optional[str] = None
    column_mappings: Optional[Dict[str, str]] = None
    sheet_name: Optional[str] = None
    force_reprocess: bool = False

class ShadowIngestResponse(BaseModel):
    status: str
    import_id: str
    source_sha256: str
    source_type: str
    dataset_type: str = 'SHADOW_REAL'
    verification_status: str = 'RECONCILED'
    readiness: str
    rows_received: int
    rows_valid: int
    rows_quarantined: int
    reconciliation_status: str

class SourceImportListItem(BaseModel):
    import_id: str
    filename: str
    source_sha256: str
    source_type: str
    dataset_type: str
    verification_status: str
    readiness: str
    rows_received: int
    rows_valid: int
    rows_quarantined: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class QuarantineItemSchema(BaseModel):
    quarantine_id: str
    import_id: str
    source_file: str
    source_row: int
    reason: str
    field_name: Optional[str] = None
    safe_value_preview: Optional[str] = None
    created_at: Optional[str] = None
