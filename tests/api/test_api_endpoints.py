# -*- coding: utf-8 -*-
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from apps.api.main import app
from apps.api.database import Base, get_db
from apps.api.services.ingestion_service import IngestionService
from apps.api.models.alerts import Alert

class TestAPIEndpoints(unittest.TestCase):
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

        db = cls.Session()
        service = IngestionService(db)
        service.ingest_synthetic_dataset("data/synthetic/damga_dataset.json", dataset_type="SYNTHETIC")
        db.close()

    def test_01_health_check(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "DAMGA-OPS API")
        self.assertIn("X-Request-ID", res.headers)

    def test_02_duplicate_synthetic_ingestion(self):
        res = self.client.post("/api/v1/ingestions/synthetic?file_path=data/synthetic/damga_dataset.json")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ALREADY_INGESTED")

    def test_03_list_ingestions(self):
        res = self.client.get("/api/v1/ingestions")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]["dataset_type"], "SYNTHETIC")

    def test_04_list_operations(self):
        res = self.client.get("/api/v1/operations?start_date=2026-06-01&end_date=2026-06-05")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data), 5)
        self.assertEqual(data[0]["business_date"], "2026-06-01")

    def test_05_get_facts_normal_date(self):
        res = self.client.get("/api/v1/facts/2026-06-12")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["business_date"], "2026-06-12")
        self.assertEqual(data["data_status"], "OK")
        self.assertEqual(data["sales"], 13092000.0)
        self.assertAlmostEqual(data["labor_ratio"], 0.3550, places=3)

    def test_06_get_facts_not_found(self):
        res = self.client.get("/api/v1/facts/1999-01-01")
        self.assertEqual(res.status_code, 404)

    def test_07_list_alerts_with_filters(self):
        res = self.client.get("/api/v1/alerts?severity=CRITICAL")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)
        for a in data:
            self.assertEqual(a["severity"], "CRITICAL")
            self.assertIsNotNone(a["evidence_id"])

    def test_08_list_alerts_invalid_severity(self):
        res = self.client.get("/api/v1/alerts?severity=SUPER_CRITICAL")
        self.assertEqual(res.status_code, 400)

    def test_09_get_daily_dashboard_normal(self):
        res = self.client.get("/api/v1/dashboard/daily/2026-06-12")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["date"], "2026-06-12")
        self.assertEqual(data["data_status"], "OK")
        self.assertFalse(data["blocked"])
        self.assertTrue(data["ai_eligible"])
        self.assertEqual(data["dataset_type"], "SYNTHETIC")
        self.assertIsNotNone(data["kpis"]["sales"])
        self.assertIsNotNone(data["kpis"]["labor_ratio"])
        
        # Verify Labor Alert is present and has evidence_id
        rule_ids = [a["rule_id"] for a in data["alerts"]]
        self.assertIn("R-LAB-01", rule_ids)
        for a in data["alerts"]:
            self.assertIsNotNone(a["evidence_id"])

    def test_10_get_daily_dashboard_ga007_partial_facts(self):
        # GA-007 (2026-08-21): Partial Facts preservation & strict dependency blocking
        res = self.client.get("/api/v1/dashboard/daily/2026-08-21")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["date"], "2026-08-21")
        self.assertEqual(data["data_status"], "DATA_INCOMPLETE")
        self.assertTrue(data["blocked"])
        self.assertFalse(data["ai_eligible"])

        # Independent facts MUST be preserved (Phase 2.1)
        self.assertEqual(data["kpis"]["sales"], 14162000.0)
        self.assertEqual(data["kpis"]["guests"], 419)
        self.assertAlmostEqual(data["kpis"]["avg_check"], 33799.52, places=1)
        self.assertEqual(data["kpis"]["labor_cost"], 3470000.0)
        self.assertAlmostEqual(data["kpis"]["labor_ratio"], 0.24502, places=3)
        self.assertEqual(data["kpi_status"]["sales"], "AVAILABLE")
        self.assertEqual(data["kpi_status"]["labor_ratio"], "AVAILABLE")


        # Dependent facts on Food_Cost MUST be Null & BLOCKED_DEPENDENCY
        self.assertIsNone(data["kpis"]["food_cost"])
        self.assertIsNone(data["kpis"]["food_cost_ratio"])
        self.assertIsNone(data["kpis"]["contribution"])
        self.assertIsNone(data["kpis"]["contribution_ratio"])
        self.assertEqual(data["kpi_status"]["food_cost"], "MISSING_INPUT")
        self.assertEqual(data["kpi_status"]["food_cost_ratio"], "BLOCKED_DEPENDENCY")
        self.assertEqual(data["kpi_status"]["contribution"], "BLOCKED_DEPENDENCY")

        # R-DQ-01 Alert present with non-null evidence_id
        rule_ids = [a["rule_id"] for a in data["alerts"]]
        self.assertIn("R-DQ-01", rule_ids)
        for a in data["alerts"]:
            self.assertIsNotNone(a["evidence_id"])

    def test_11_dashboard_summary_with_coverage(self):
        # Summary API uses independent denominator for each KPI and includes Coverage metadata
        res = self.client.get("/api/v1/dashboard/summary?start_date=2026-06-01&end_date=2026-08-31")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_days"], 92)
        self.assertEqual(data["data_complete_days"], 91)
        self.assertEqual(data["data_incomplete_days"], 1)

        # Exact Golden Source Sales Sum: 1,058,152,000 KRW
        self.assertEqual(data["total_sales"], 1058152000.0)
        self.assertAlmostEqual(data["average_daily_sales"], 11501652.17, places=2)

        # Coverage verification
        self.assertEqual(data["coverage"]["sales"]["available_days"], 92)
        self.assertEqual(data["coverage"]["labor_ratio"]["available_days"], 92)
        self.assertEqual(data["coverage"]["food_cost_ratio"]["available_days"], 91)
        self.assertEqual(data["coverage"]["contribution_ratio"]["available_days"], 91)

    def test_12_evidence_api_endpoint(self):
        # Fetch one alert from DB to get a valid evidence_id
        db = self.Session()
        alert = db.query(Alert).first()
        ev_id = alert.evidence_id
        db.close()

        # Valid evidence_id -> 200 OK
        res = self.client.get(f"/api/v1/evidence/{ev_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["evidence_id"], ev_id)
        self.assertEqual(data["rule_id"], alert.rule_id)

        # Invalid evidence_id -> 404 Not Found
        res_404 = self.client.get("/api/v1/evidence/NON_EXISTENT_ID")
        self.assertEqual(res_404.status_code, 404)

if __name__ == '__main__':
    unittest.main()
