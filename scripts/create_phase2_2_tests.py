# -*- coding: utf-8 -*-
import os

files = {}

# 1. Evidence Cryptographic Integrity Test Suite
files['tests/storage/test_evidence_integrity.py'] = """# -*- coding: utf-8 -*-
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
"""

# 2. Missing-Value Semantics Unit Test Suite
files['tests/unit/test_missing_semantics.py'] = """# -*- coding: utf-8 -*-
import unittest
from domains.pipeline import process_daily_record
from domains.customer.facts import calculate_daily_rating, calculate_complaints, calculate_review_count

class TestMissingSemantics(unittest.TestCase):
    def test_data01_service_kg_zero_is_available(self):
        # DATA-01: Service_kg = 0 -> AVAILABLE, value: 0.0
        row = {
            'Date': '46200',
            'Sales': 10000000,
            'Guests': 200,
            'Labor_Cost': 2500000,
            'Food_Cost': 3000000,
            'Incoming_kg': 100,
            'Sold_kg': 80,
            'Service_kg': 0,
            'Waste_kg': 2,
            'Actual_End_kg': 18
        }
        res = process_daily_record(row)
        self.assertEqual(res['facts']['service_kg'], 0.0)
        self.assertEqual(res['facts']['kpi_status']['service_kg'], 'AVAILABLE')
        self.assertEqual(res['facts']['theory_end_kg'], 18.0)
        self.assertEqual(res['facts']['variance_kg'], 0.0)

    def test_data02_service_kg_none_blocks_theory_end_when_not_provided(self):
        # DATA-02: Service_kg = None and Theory_End_kg = None -> Theory End & Variance blocked
        row = {
            'Date': '46200',
            'Sales': 10000000,
            'Guests': 200,
            'Labor_Cost': 2500000,
            'Food_Cost': 3000000,
            'Incoming_kg': 100,
            'Sold_kg': 80,
            'Service_kg': None,
            'Waste_kg': 2,
            'Actual_End_kg': 18
        }
        res = process_daily_record(row)
        self.assertIsNone(res['facts']['service_kg'])
        self.assertEqual(res['facts']['kpi_status']['service_kg'], 'NOT_PROVIDED')
        self.assertIsNone(res['facts']['theory_end_kg'])
        self.assertIsNone(res['facts']['variance_kg'])
        self.assertEqual(res['facts']['kpi_status']['theory_end_kg'], 'BLOCKED_DEPENDENCY')
        self.assertEqual(res['facts']['kpi_status']['inventory_variance'], 'BLOCKED_DEPENDENCY')

    def test_data03_service_kg_none_with_provided_theory_end(self):
        # DATA-03: Service_kg = None but Theory_End_kg provided -> Variance calculable
        row = {
            'Date': '46200',
            'Sales': 10000000,
            'Guests': 200,
            'Labor_Cost': 2500000,
            'Food_Cost': 3000000,
            'Incoming_kg': 100,
            'Sold_kg': 80,
            'Service_kg': None,
            'Waste_kg': 2,
            'Actual_End_kg': 18,
            'Theory_End_kg': 19.5
        }
        res = process_daily_record(row)
        self.assertIsNone(res['facts']['service_kg'])
        self.assertEqual(res['facts']['kpi_status']['service_kg'], 'NOT_PROVIDED')
        self.assertEqual(res['facts']['theory_end_kg'], 19.5)
        self.assertEqual(res['facts']['variance_kg'], -1.5)
        self.assertEqual(res['facts']['kpi_status']['theory_end_kg'], 'AVAILABLE')
        self.assertEqual(res['facts']['kpi_status']['inventory_variance'], 'AVAILABLE')

    def test_data04_complaints_none_distinct_from_zero(self):
        # DATA-04: Complaints None != 0
        self.assertIsNone(calculate_complaints(None))
        self.assertIsNone(calculate_complaints(''))
        self.assertEqual(calculate_complaints(0), 0)
        self.assertEqual(calculate_complaints('0'), 0)

    def test_data05_review_count_none_distinct_from_zero(self):
        # DATA-05: Review_Count None != 0
        self.assertIsNone(calculate_review_count(None))
        self.assertIsNone(calculate_review_count(''))
        self.assertEqual(calculate_review_count(0), 0)
        self.assertEqual(calculate_review_count('0'), 0)

    def test_data06_rating_none_distinct_from_zero(self):
        # DATA-06: Rating None != 0.0
        self.assertIsNone(calculate_daily_rating(None))
        self.assertIsNone(calculate_daily_rating(''))
        self.assertEqual(calculate_daily_rating(0.0), 0.0)
        self.assertEqual(calculate_daily_rating('4.5'), 4.5)

if __name__ == '__main__':
    unittest.main()
"""

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

print(f"Successfully generated {len(files)} Phase 2.2 test files.")

