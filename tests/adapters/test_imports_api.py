# -*- coding: utf-8 -*-
import json
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_api_profile_file():
    res = client.post("/api/v1/imports/profile", json={
        "file_path": "fixtures/source_samples/pos_generic_good.csv"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["filename"] == "pos_generic_good.csv"
    assert data["row_count"] == 3
    assert len(data["column_names"]) >= 10
    assert "file_sha256" in data

def test_api_suggest_mapping():
    res = client.post("/api/v1/imports/map", json={
        "source_type": "POS",
        "columns": ["매출일자", "영수증번호", "실매출액", "메뉴명", "수량"]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["source_type"] == "POS"
    assert len(data["suggestions"]) == 5
    assert data["suggestions"][0]["confidence"] == "HIGH"

def test_api_confirm_mapping_and_get():
    confirm_payload = {
        "mapping_id": "MAP-API-POS-01",
        "source_type": "POS",
        "mapping_version": "1.0.0",
        "column_mappings": {
            "매출일자": "business_date",
            "영수증번호": "receipt_id",
            "메뉴코드": "menu_id",
            "메뉴명": "menu_name",
            "수량": "quantity",
            "실매출액": "net_sales"
        },
        "reviewer_name": "TEST_ADMIN"
    }
    res = client.post("/api/v1/mappings/confirm", json=confirm_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mapping_id"] == "MAP-API-POS-01"
    assert data["status"] == "CONFIRMED"

    # Get manifest
    get_res = client.get("/api/v1/mappings/MAP-API-POS-01")
    assert get_res.status_code == 200
    assert get_res.json()["mapping_id"] == "MAP-API-POS-01"

def test_api_validate_file():
    res = client.post("/api/v1/imports/validate", json={
        "file_path": "fixtures/source_samples/pos_generic_good.csv",
        "source_type": "POS",
        "mapping_id": "MAP-API-POS-01"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["rows_received"] == 3
    assert data["rows_mapped"] == 3
    assert data["rows_quarantined"] == 0
    assert data["readiness"] == "SHADOW_READY"

def test_api_shadow_ingest_and_idempotency():
    ingest_payload = {
        "file_path": "fixtures/source_samples/pos_generic_good.csv",
        "source_type": "POS",
        "mapping_id": "MAP-API-POS-01",
        "force_reprocess": True
    }
    res = client.post("/api/v1/imports/ingest-shadow", json=ingest_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["dataset_type"] == "SHADOW_REAL"
    import_id = data["import_id"]

    # Test idempotency (force_reprocess = False)
    ingest_payload["force_reprocess"] = False
    res_idem = client.post("/api/v1/imports/ingest-shadow", json=ingest_payload)
    assert res_idem.status_code == 200
    assert res_idem.json()["status"] == "ALREADY_INGESTED"

    # Test import details, quality, quarantine, reconciliation
    det_res = client.get(f"/api/v1/imports/{import_id}")
    assert det_res.status_code == 200
    assert det_res.json()["import_id"] == import_id

    q_res = client.get(f"/api/v1/imports/{import_id}/quality")
    assert q_res.status_code == 200
    assert q_res.json()["completeness_score"] == 1.0

    qr_res = client.get(f"/api/v1/imports/{import_id}/quarantine")
    assert qr_res.status_code == 200
    assert isinstance(qr_res.json(), list)

    rec_res = client.get(f"/api/v1/imports/{import_id}/reconciliation")
    assert rec_res.status_code == 200
    assert rec_res.json()["overall_status"] == "MATCH"

def test_api_list_imports():
    res = client.get("/api/v1/imports")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 1

