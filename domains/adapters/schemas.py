# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CanonicalPOSRecord(BaseModel):
    business_date: str
    transaction_time: Optional[str] = None
    receipt_id: str
    table_id: Optional[str] = None
    menu_id: str
    menu_name: str
    quantity: int
    gross_sales: float
    discount: float = 0.0
    net_sales: float
    guests: Optional[int] = None
    payment_type: Optional[str] = None
    cancelled: bool = False
    void_reason: Optional[str] = None
    channel: Optional[str] = None
    order_type: Optional[str] = None
    source_system: str = 'GENERIC'
    source_file: str
    source_row: int

class CanonicalAttendanceRecord(BaseModel):
    business_date: str
    employee_id: str
    department: str
    role: str
    clock_in: str
    clock_out: str
    worked_minutes: int
    regular_minutes: int
    overtime_minutes: int = 0
    labor_cost: Optional[float] = None
    source_system: str = 'GENERIC'
    source_file: str
    source_row: int

class CanonicalPurchaseRecord(BaseModel):
    purchase_date: str
    supplier_id: str
    category: str
    item_id: str
    item_name: str
    quantity: float
    unit: str
    unit_price: float
    amount: float
    tax: float = 0.0
    source_amount: Optional[float] = None
    calculated_amount: Optional[float] = None
    invoice_id: Optional[str] = None
    source_system: str = 'GENERIC'
    source_file: str
    source_row: int

class CanonicalInventoryRecord(BaseModel):
    business_date: str
    item_id: str
    item_name: str
    opening_qty: float
    incoming_qty: float
    sold_qty: float
    service_qty: Optional[float] = None
    waste_qty: Optional[float] = None
    staff_meal_qty: Optional[float] = None
    transfer_qty: Optional[float] = None
    theory_end_qty: float
    actual_end_qty: float
    unit: str
    source_system: str = 'GENERIC'
    source_file: str
    source_row: int

class QuarantineRecord(BaseModel):
    quarantine_id: str
    source_file: str
    source_row: int
    reason: str
    field_name: Optional[str] = None
    safe_value_preview: Optional[str] = None

class DataProfile(BaseModel):
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
    numeric_ranges: Dict[str, Dict[str, float]] = {}
    sample_values_masked: Dict[str, List[Any]] = {}
    sensitive_columns_detected: List[str] = []

class MappingSuggestionItem(BaseModel):
    source_column: str
    suggested_canonical_field: Optional[str] = None
    confidence: str = 'LOW'  # HIGH, MEDIUM, LOW, UNMAPPED
    status: str = 'SUGGESTED' # SUGGESTED, CONFIRMED, REJECTED

class MappingManifest(BaseModel):
    mapping_id: str
    source_type: str # POS, ATTENDANCE, PURCHASE, INVENTORY
    mapping_version: str = '1.0.0'
    status: str = 'SUGGESTED' # SUGGESTED, CONFIRMED, REJECTED
    column_mappings: Dict[str, str] = {} # source_column -> canonical_field
    transforms: Dict[str, str] = {}
    created_at: Optional[str] = None

class ReconciliationMetric(BaseModel):
    name: str
    source_value: float
    calculated_value: float
    diff_abs: float
    diff_pct: float
    status: str # MATCH, MINOR_MISMATCH, MAJOR_MISMATCH, NOT_COMPARABLE
    detail: Optional[str] = None

class ReconciliationReport(BaseModel):
    reconciliation_id: str
    import_id: str
    source_type: str
    overall_status: str # MATCH, MINOR_MISMATCH, MAJOR_MISMATCH, NOT_COMPARABLE
    metrics: List[ReconciliationMetric] = []
    generated_at: Optional[str] = None

class RealDataQualityReport(BaseModel):
    import_id: str
    rows_received: int
    rows_valid: int
    rows_quarantined: int
    rows_duplicate: int
    completeness_score: float
    date_coverage_start: Optional[str] = None
    date_coverage_end: Optional[str] = None
    mapping_status: str
    reconciliation_status: str
    sensitive_columns_count: int
    readiness: str # BLOCKED, REVIEW_REQUIRED, SHADOW_READY, REAL_READY

class MappingResult(BaseModel):
    source_type: str
    source_system: str
    rows_received: int
    rows_mapped: int
    rows_quarantined: int
    mapping_version: str
    canonical_records: List[Dict[str, Any]] = []
    quarantine_records: List[QuarantineRecord] = []
    issues: List[str] = []
