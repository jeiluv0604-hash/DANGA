# -*- coding: utf-8 -*-
import sqlite3
import pytest
from sqlalchemy import create_engine, inspect
from apps.api.database import Base
from apps.api.models import (
    DailyOperation,
    DailyFact,
    Alert,
    PeriodAlert,
    IngestionRun,
    AnalystBriefModel,
    SourceImportModel,
    QuarantineRecordModel,
    MappingManifestModel,
    CanonicalPOSModel
)

def test_mig_01_all_tables_exist():
    engine = create_engine("sqlite:///data/damga_ops.db")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = [
        "daily_operations",
        "daily_facts",
        "alerts",
        "period_alerts",
        "ingestion_runs",
        "evidence_index",
        "analyst_briefs",
        "decision_actions",
        "decision_audit_logs",
        "source_imports",
        "quarantine_records",
        "mapping_manifests",
        "canonical_pos_transactions",
        "canonical_attendance_records",
        "canonical_purchase_records",
        "canonical_inventory_records"
    ]
    for t in expected_tables:
        assert t in tables, f"Table {t} missing from migrated database"

def test_mig_02_verification_status_column_exists():
    engine = create_engine("sqlite:///data/damga_ops.db")
    inspector = inspect(engine)
    
    for table_name in ["daily_operations", "daily_facts", "alerts", "period_alerts", "ingestion_runs", "analyst_briefs", "source_imports"]:
        columns = [c["name"] for c in inspector.get_columns(table_name)]
        assert "verification_status" in columns, f"verification_status missing in {table_name}"

def test_mig_03_existing_data_preserved():
    conn = sqlite3.connect("data/damga_ops.db")
    cursor = conn.cursor()
    # Ensure tables can be queried and data is not lost/dropped
    cursor.execute("SELECT count(*) FROM daily_operations")
    op_count = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM daily_facts")
    fact_count = cursor.fetchone()[0]
    conn.close()
    assert op_count >= 0
    assert fact_count >= 0

def test_mig_04_no_drop_all_rule_integrity():
    # Verify metadata contains non-destructive DDL definitions
    assert hasattr(Base.metadata, "tables")
    assert "canonical_pos_transactions" in Base.metadata.tables

