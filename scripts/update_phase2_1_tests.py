# -*- coding: utf-8 -*-
import os

files = {}

# 1. API Endpoints Test
files['tests/api/test_api_endpoints.py'] = """# -*- coding: utf-8 -*-
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
        self.assertEqual(data["kpis"]["sales"], 1628000.0)
        self.assertEqual(data["kpis"]["guests"], 42)
        self.assertAlmostEqual(data["kpis"]["avg_check"], 38761.90, places=1)
        self.assertEqual(data["kpis"]["labor_cost"], 1162000.0)
        self.assertAlmostEqual(data["kpis"]["labor_ratio"], 0.71376, places=3)
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
"""

# 2. Storage Tests
files['tests/storage/test_storage.py'] = """# -*- coding: utf-8 -*-
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from apps.api.database import Base
from apps.api.models.ingestion import IngestionRun
from apps.api.models.operations import DailyOperation
from apps.api.models.facts import DailyFact
from apps.api.models.alerts import Alert, PeriodAlert
from apps.api.models.evidence import EvidenceIndex
from apps.api.services.ingestion_service import IngestionService

class TestStorageLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        cls.Session = sessionmaker(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()

    def tearDown(self):
        self.db.close()

    def test_01_synthetic_ingestion_and_storage(self):
        dataset_path = "data/synthetic/damga_dataset.json"
        service = IngestionService(self.db)
        res = service.ingest_synthetic_dataset(file_path=dataset_path, dataset_type="SYNTHETIC")

        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(res["row_count"], 92)
        self.assertEqual(res["valid_row_count"], 91)
        self.assertEqual(res["blocked_row_count"], 1)

        # Check Ingestion Run record
        run = self.db.query(IngestionRun).filter_by(ingestion_id=res["ingestion_id"]).first()
        self.assertIsNotNone(run)
        self.assertEqual(run.status, "COMPLETED")
        self.assertEqual(run.dataset_type, "SYNTHETIC")

        # Check Operations count
        ops_count = self.db.query(DailyOperation).count()
        self.assertEqual(ops_count, 92)

        # Check Facts count
        facts_count = self.db.query(DailyFact).count()
        self.assertEqual(facts_count, 92)

        # Check Partial Facts on 2026-08-21 (GA-007)
        dq_fact = self.db.query(DailyFact).filter_by(business_date="2026-08-21").first()
        self.assertIsNotNone(dq_fact)
        self.assertEqual(dq_fact.data_status, "DATA_INCOMPLETE")
        self.assertEqual(dq_fact.sales, 1628000.0)
        self.assertEqual(dq_fact.guests, 42)
        self.assertEqual(dq_fact.labor_cost, 1162000.0)
        self.assertAlmostEqual(dq_fact.labor_ratio, 0.71376, places=3)
        self.assertIsNone(dq_fact.food_cost)
        self.assertIsNone(dq_fact.contribution)

        # Check Evidence Linkage & Referential Integrity
        alerts = self.db.query(Alert).all()
        for a in alerts:
            self.assertIsNotNone(a.evidence_id)
            ev = self.db.query(EvidenceIndex).filter_by(evidence_id=a.evidence_id).first()
            self.assertIsNotNone(ev, f"Orphan alert without evidence: {a.alert_id}")

        period_alerts = self.db.query(PeriodAlert).all()
        for pa in period_alerts:
            self.assertIsNotNone(pa.evidence_id)
            ev = self.db.query(EvidenceIndex).filter_by(evidence_id=pa.evidence_id).first()
            self.assertIsNotNone(ev, f"Orphan period alert without evidence: {pa.alert_id}")

    def test_02_idempotency_duplicate_ingestion(self):
        dataset_path = "data/synthetic/damga_dataset.json"
        service = IngestionService(self.db)
        res = service.ingest_synthetic_dataset(file_path=dataset_path, dataset_type="SYNTHETIC")
        self.assertEqual(res["status"], "ALREADY_INGESTED")
        
        # Row counts must not increase
        self.assertEqual(self.db.query(DailyOperation).count(), 92)
        self.assertEqual(self.db.query(DailyFact).count(), 92)

if __name__ == '__main__':
    unittest.main()
"""

# 3. Persistence Regression Test
files['tests/persistence/test_persistence_regression.py'] = """# -*- coding: utf-8 -*-
import json
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from apps.api.database import Base
from apps.api.models.facts import DailyFact
from apps.api.models.alerts import Alert
from apps.api.services.ingestion_service import IngestionService
from domains.pipeline import run_full_pipeline

class TestPersistenceRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        cls.Session = sessionmaker(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        with open("data/synthetic/damga_dataset.json", "r", encoding="utf-8") as f:
            cls.dataset = json.load(f)

        header = cls.dataset["Daily_Operations"][0]
        cls.raw_rows = [dict(zip(header, r)) for r in cls.dataset["Daily_Operations"][1:]]

        # 1. In-Memory Domain Pipeline Execution
        cls.pipeline_results = run_full_pipeline(cls.raw_rows)

        # 2. Database Ingestion
        db = cls.Session()
        service = IngestionService(db)
        service.ingest_synthetic_dataset("data/synthetic/damga_dataset.json", dataset_type="SYNTHETIC")
        cls.db_facts = {f.business_date: f for f in db.query(DailyFact).all()}
        cls.db_alerts = db.query(Alert).all()
        db.close()

    def test_facts_persistence_regression_100_percent_match(self):
        # In-Memory Facts vs Database DailyFact 100% match validation
        self.assertEqual(len(self.pipeline_results), len(self.db_facts))

        for res in self.pipeline_results:
            b_date = res["date"]
            db_f = self.db_facts[b_date]

            self.assertEqual(res["data_status"], db_f.data_status)
            pf = res["facts"]
            self.assertEqual(pf["sales"], db_f.sales)
            self.assertEqual(pf["guests"], db_f.guests)
            self.assertEqual(pf["avg_check"], db_f.avg_check)
            self.assertEqual(pf["labor_cost"], db_f.labor_cost)
            self.assertEqual(pf["labor_ratio"], db_f.labor_ratio)
            self.assertEqual(pf["food_cost"], db_f.food_cost)
            self.assertEqual(pf["food_cost_ratio"], db_f.food_cost_ratio)
            self.assertEqual(pf["variance_kg"], db_f.variance_kg)
            self.assertEqual(pf["waste_ratio"], db_f.waste_ratio)
            self.assertEqual(pf["rating"], db_f.rating)
            self.assertEqual(pf["complaints"], db_f.complaints)
            self.assertEqual(pf["contribution"], db_f.contribution)
            self.assertEqual(pf["contribution_ratio"], db_f.contribution_ratio)

    def test_alerts_persistence_regression(self):
        # In-Memory Alerts vs Database Alert 100% match validation
        pipeline_alerts = []
        for r in self.pipeline_results:
            for a in r.get("alerts", []):
                pipeline_alerts.append((r["date"], a["rule_id"], a["severity"]))

        db_alerts = [(a.business_date, a.rule_id, a.severity) for a in self.db_alerts]

        self.assertEqual(sorted(pipeline_alerts), sorted(db_alerts))

if __name__ == '__main__':
    unittest.main()
"""

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

print(f"Successfully generated {len(files)} Phase 2.1 updated test files.")

