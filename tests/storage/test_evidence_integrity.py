# -*- coding: utf-8 -*-
import hashlib
import json
import os
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from apps.api.main import app
from apps.api.database import Base, get_db
from apps.api.models.evidence import EvidenceIndex
from apps.api.models.alerts import Alert, PeriodAlert
from apps.api.services.ingestion_service import IngestionService
from apps.api.routes.evidence import verify_evidence_integrity

class TestEvidenceIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        cls.Session = sessionmaker(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

        cls.db = cls.Session()
        service = IngestionService(cls.db)
        cls.ingest_res = service.ingest_synthetic_dataset("data/synthetic/damga_dataset.json", dataset_type="SYNTHETIC")

        with open("data/synthetic/damga_dataset.json", "rb") as f:
            cls.expected_dataset_sha = hashlib.sha256(f.read()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_ev01_file_actual_sha_matches_stored(self):
        # EV-01: All stored evidence files on disk match their stored file_sha256
        ev_records = self.db.query(EvidenceIndex).all()
        self.assertGreater(len(ev_records), 0)
        for ev in ev_records:
            self.assertTrue(os.path.exists(ev.file_path), f"File missing: {ev.file_path}")
            with open(ev.file_path, "rb") as f:
                actual_sha = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(actual_sha, ev.file_sha256, f"Hash mismatch for {ev.evidence_id}")

    def test_ev02_dataset_sha_matches_source(self):
        # EV-02: All evidence records point to the valid source dataset SHA-256
        ev_records = self.db.query(EvidenceIndex).all()
        for ev in ev_records:
            self.assertEqual(ev.dataset_sha256, self.expected_dataset_sha)

    def test_ev03_file_sha_and_dataset_sha_are_distinct(self):
        # EV-03: file_sha256 and dataset_sha256 are computed separately and distinct
        ev_records = self.db.query(EvidenceIndex).all()
        for ev in ev_records:
            self.assertNotEqual(ev.file_sha256, ev.dataset_sha256, f"file_sha256 should not be identical to dataset_sha256: {ev.evidence_id}")

    def test_ev04_tampered_evidence_detected_as_invalid(self):
        # EV-04: If file content is modified, verify returns INVALID
        temp_ev_id = "EV-TEMP-TEST-001"
        temp_path = f"evidence/{temp_ev_id}.json"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump({"test": "initial"}, f)

        with open(temp_path, "rb") as f:
            orig_sha = hashlib.sha256(f.read()).hexdigest()

        temp_model = EvidenceIndex(
            evidence_id=temp_ev_id,
            evidence_type="DAILY_ALERT",
            business_date="2026-06-01",
            rule_id="R-TEST",
            file_path=temp_path,
            file_sha256=orig_sha,
            dataset_sha256=self.expected_dataset_sha
        )
        self.db.add(temp_model)
        self.db.commit()

        # 1. Before tampering -> VALID
        res_before = verify_evidence_integrity(self.db, temp_ev_id)
        self.assertEqual(res_before["integrity"], "VALID")

        # 2. Tamper file
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump({"test": "tampered_data"}, f)

        # 3. After tampering -> INVALID
        res_after = verify_evidence_integrity(self.db, temp_ev_id)
        self.assertEqual(res_after["integrity"], "INVALID")
        self.assertNotEqual(res_after["actual_sha256"], res_after["stored_sha256"])

        # Cleanup
        self.db.delete(temp_model)
        self.db.commit()
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_ev05_missing_file_detected(self):
        # EV-05: If evidence index exists but file is missing -> MISSING_FILE
        temp_ev_id = "EV-TEMP-MISSING-001"
        temp_model = EvidenceIndex(
            evidence_id=temp_ev_id,
            evidence_type="DAILY_ALERT",
            business_date="2026-06-01",
            rule_id="R-TEST",
            file_path="evidence/non_existent_file.json",
            file_sha256="dummy_hash_12345",
            dataset_sha256=self.expected_dataset_sha
        )
        self.db.add(temp_model)
        self.db.commit()

        res = verify_evidence_integrity(self.db, temp_ev_id)
        self.assertEqual(res["integrity"], "MISSING_FILE")
        self.assertFalse(res["exists"])

        self.db.delete(temp_model)
        self.db.commit()

    def test_ev06_verify_api_endpoint(self):
        # EV-06: GET /api/v1/evidence/{evidence_id}/verify returns 200 and VALID
        ev = self.db.query(EvidenceIndex).first()
        res = self.client.get(f"/api/v1/evidence/{ev.evidence_id}/verify")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["evidence_id"], ev.evidence_id)
        self.assertEqual(data["integrity"], "VALID")
        self.assertTrue(data["exists"])

    def test_ev07_verify_api_404_for_invalid_id(self):
        # EV-07: 404 for non-existent evidence ID
        res = self.client.get("/api/v1/evidence/NON_EXISTENT_ID/verify")
        self.assertEqual(res.status_code, 404)

    def test_ev08_all_alerts_and_period_alerts_have_valid_evidence(self):
        # Referential integrity check: all alerts have VALID evidence on disk
        alerts = self.db.query(Alert).all()
        for a in alerts:
            self.assertIsNotNone(a.evidence_id)
            res = verify_evidence_integrity(self.db, a.evidence_id)
            self.assertIsNotNone(res)
            self.assertEqual(res["integrity"], "VALID", f"Alert evidence invalid: {a.alert_id}")

        p_alerts = self.db.query(PeriodAlert).all()
        for pa in p_alerts:
            self.assertIsNotNone(pa.evidence_id)
            res = verify_evidence_integrity(self.db, pa.evidence_id)
            self.assertIsNotNone(res)
            self.assertEqual(res["integrity"], "VALID", f"Period alert evidence invalid: {pa.alert_id}")

if __name__ == '__main__':
    unittest.main()
