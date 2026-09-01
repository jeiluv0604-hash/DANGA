# -*- coding: utf-8 -*-
import os
import json
import pytest
from domains.adapters.csv_adapter import GenericCSVAdapter
from domains.adapters.xlsx_adapter import GenericXLSXAdapter
from domains.adapters.schemas import MappingManifest

def test_adapter_01_valid_pos_csv_mapping():
    adapter = GenericCSVAdapter()
    manifest_data = json.load(open("mappings/pos_generic_v1.json", encoding="utf-8"))
    manifest = MappingManifest(**manifest_data)
    res = adapter.map_to_canonical("fixtures/source_samples/pos_generic_good.csv", manifest)
    assert res.source_type == "POS"
    assert res.rows_received == 3
    assert res.rows_mapped == 3
    assert res.rows_quarantined == 0
    assert len(res.canonical_records) == 3
    assert res.canonical_records[0]["business_date"] == "2026-10-01"
    assert res.canonical_records[0]["net_sales"] == 70000

def test_adapter_02_different_korean_column_names():
    adapter = GenericCSVAdapter()
    custom_manifest = MappingManifest(
        mapping_id="MAP-POS-CUSTOM",
        source_type="POS",
        column_mappings={
            "매출일자": "business_date",
            "영수증번호": "receipt_id",
            "메뉴코드": "menu_id",
            "메뉴명": "menu_name",
            "수량": "quantity",
            "실매출액": "net_sales"
        }
    )
    res = adapter.map_to_canonical("fixtures/source_samples/pos_generic_good.csv", custom_manifest)
    assert res.rows_mapped == 3
    assert res.canonical_records[0]["receipt_id"] == "REC-1001-01"

def test_adapter_03_missing_required_column():
    adapter = GenericCSVAdapter()
    manifest_data = json.load(open("mappings/pos_generic_v1.json", encoding="utf-8"))
    manifest = MappingManifest(**manifest_data)
    # File missing 메뉴코드
    res = adapter.map_to_canonical("fixtures/source_samples/pos_missing_column.csv", manifest)
    assert res.rows_quarantined == 3
    assert res.rows_mapped == 0
    assert all(q.reason == "MISSING_REQUIRED_FIELD" for q in res.quarantine_records)

def test_adapter_04_invalid_date_format():
    adapter = GenericCSVAdapter()
    manifest_data = json.load(open("mappings/pos_generic_v1.json", encoding="utf-8"))
    manifest = MappingManifest(**manifest_data)
    res = adapter.map_to_canonical("fixtures/source_samples/pos_bad_dates.csv", manifest)
    assert res.rows_quarantined >= 2
    assert any(q.reason == "INVALID_DATE" for q in res.quarantine_records)

def test_adapter_05_invalid_numeric():
    adapter = GenericCSVAdapter()
    # Create temp bad csv with negative sales and 0 quantity
    import pandas as pd
    bad_df = pd.DataFrame([
        {'매출일자': '2026-10-01', '영수증번호': 'R1', '메뉴코드': 'M1', '수량': 0, '실매출액': 1000},
        {'매출일자': '2026-10-01', '영수증번호': 'R2', '메뉴코드': 'M2', '수량': 1, '실매출액': -5000}
    ])
    bad_path = "fixtures/source_samples/temp_bad_numeric.csv"
    bad_df.to_csv(bad_path, index=False)
    
    manifest_data = json.load(open("mappings/pos_generic_v1.json", encoding="utf-8"))
    manifest = MappingManifest(**manifest_data)
    res = adapter.map_to_canonical(bad_path, manifest)
    assert res.rows_quarantined == 2
    reasons = [q.reason for q in res.quarantine_records]
    assert "INVALID_NUMBER" in reasons or "NEGATIVE_SALES" in reasons
    if os.path.exists(bad_path):
        os.remove(bad_path)

def test_adapter_06_duplicate_receipt():
    adapter = GenericCSVAdapter()
    manifest_data = json.load(open("mappings/pos_generic_v1.json", encoding="utf-8"))
    manifest = MappingManifest(**manifest_data)
    res = adapter.map_to_canonical("fixtures/source_samples/pos_duplicates.csv", manifest)
    assert res.rows_quarantined >= 1
    assert any(q.reason == "DUPLICATE_RECEIPT" for q in res.quarantine_records)

def test_adapter_07_attendance_missing_labor_cost():
    adapter = GenericXLSXAdapter()
    manifest_data = json.load(open("mappings/attendance_generic_v1.json", encoding="utf-8"))
    manifest = MappingManifest(**manifest_data)
    res = adapter.map_to_canonical("fixtures/source_samples/attendance_missing_cost.xlsx", manifest)
    assert res.rows_mapped == 2
    assert res.canonical_records[0]["labor_cost"] is None

def test_adapter_08_attendance_invalid_clock_range():
    adapter = GenericXLSXAdapter()
    manifest_data = json.load(open("mappings/attendance_generic_v1.json", encoding="utf-8"))
    manifest = MappingManifest(**manifest_data)
    res = adapter.map_to_canonical("fixtures/source_samples/attendance_bad_time.xlsx", manifest)
    assert res.rows_quarantined == 1
    assert res.quarantine_records[0].reason == "INVALID_TIME_RANGE"

def test_adapter_09_purchase_good_and_detection():
    adapter = GenericXLSXAdapter()
    manifest_data = json.load(open("mappings/purchases_generic_v1.json", encoding="utf-8"))
    manifest = MappingManifest(**manifest_data)
    res = adapter.map_to_canonical("fixtures/source_samples/purchases_good.xlsx", manifest)
    assert res.rows_mapped == 2
    assert res.rows_quarantined == 0

def test_adapter_10_inventory_missing_service():
    adapter = GenericXLSXAdapter()
    manifest_data = json.load(open("mappings/inventory_generic_v1.json", encoding="utf-8"))
    manifest = MappingManifest(**manifest_data)
    res = adapter.map_to_canonical("fixtures/source_samples/inventory_missing_service.xlsx", manifest)
    assert res.rows_mapped == 1
    assert res.canonical_records[0]["service_qty"] is None

def test_adapter_11_unknown_unit_detection():
    adapter = GenericXLSXAdapter()
    manifest_data = json.load(open("mappings/purchases_generic_v1.json", encoding="utf-8"))
    manifest = MappingManifest(**manifest_data)
    import pandas as pd
    bad_unit_df = pd.DataFrame([
        {'매입일자': '2026-10-01', '거래처코드': 'V1', '품목코드': 'I1', '수량': 10, '단위': 'UNKNOWN_CUSTOM_UNIT', '단가': 1000, '공급가액': 10000}
    ])
    temp_path = "fixtures/source_samples/temp_bad_unit.xlsx"
    bad_unit_df.to_excel(temp_path, index=False)
    res = adapter.map_to_canonical(temp_path, manifest)
    assert res.rows_quarantined == 1
    assert res.quarantine_records[0].reason == "UNIT_UNKNOWN"
    if os.path.exists(temp_path):
        os.remove(temp_path)

def test_adapter_12_detect_source_type():
    csv_ad = GenericCSVAdapter()
    xlsx_ad = GenericXLSXAdapter()
    assert csv_ad.detect_source_type("fixtures/source_samples/pos_generic_good.csv") == "POS"
    assert xlsx_ad.detect_source_type("fixtures/source_samples/attendance_good.xlsx") == "ATTENDANCE"
    assert xlsx_ad.detect_source_type("fixtures/source_samples/purchases_good.xlsx") == "PURCHASE"
    assert xlsx_ad.detect_source_type("fixtures/source_samples/inventory_good.xlsx") == "INVENTORY"

