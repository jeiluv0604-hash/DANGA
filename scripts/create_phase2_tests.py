# -*- coding: utf-8 -*-
import os

files = {}

# 1. Storage Tests
files['tests/storage/test_storage.py'] = """# -*- coding: utf-8 -*-
import os
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.database import Base
from apps.api.models.ingestion import IngestionRun
from apps.api.models.operations import DailyOperation
from apps.api.models.facts import DailyFact
from apps.api.models.alerts import Alert, PeriodAlert
from apps.api.services.ingestion_service import IngestionService
from apps.api.repositories.facts_repository import FactsRepository
from apps.api.repositories.alerts_repository import AlertsRepository

class TestStorageLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        cls.Session = sessionmaker(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()

    def tearDown(self):
        self.db.close()

    def test_synthetic_ingestion_and_storage(self):
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

        # Check Data Incomplete Row (2026-08-21)
        dq_fact = self.db.query(DailyFact).filter_by(business_date="2026-08-21").first()
        self.assertIsNotNone(dq_fact)
        self.assertEqual(dq_fact.data_status, "DATA_INCOMPLETE")
        self.assertIsNone(dq_fact.food_cost)
        self.assertIsNone(dq_fact.contribution)

        # Check Alerts
        dq_alert = self.db.query(Alert).filter_by(business_date="2026-08-21", rule_id="R-DQ-01").first()
        self.assertIsNotNone(dq_alert)
        self.assertEqual(dq_alert.severity, "CRITICAL")

        # Check Period Alerts
        period_alerts = self.db.query(PeriodAlert).all()
        self.assertGreaterEqual(len(period_alerts), 2)
        rule_ids = [pa.rule_id for pa in period_alerts]
        self.assertIn("R-FC-01-PERIOD", rule_ids)
        self.assertIn("R-PRO-01", rule_ids)

    def test_idempotency_duplicate_ingestion(self):
        dataset_path = "data/synthetic/damga_dataset.json"
        service = IngestionService(self.db)
        # First call was already completed in test_synthetic_ingestion_and_storage (shared in-memory DB)
        res = service.ingest_synthetic_dataset(file_path=dataset_path, dataset_type="SYNTHETIC")
        self.assertEqual(res["status"], "ALREADY_INGESTED")
        
        # Row counts must not increase
        self.assertEqual(self.db.query(DailyOperation).count(), 92)
        self.assertEqual(self.db.query(DailyFact).count(), 92)

if __name__ == '__main__':
    unittest.main()
"""

# 2. API Endpoint Tests
files['tests/api/test_api_endpoints.py'] = """# -*- coding: utf-8 -*-
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.main import app
from apps.api.database import Base, get_db
from apps.api.services.ingestion_service import IngestionService

class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
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

        # Ingest Golden Dataset for testing
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
        self.assertEqual(data["sales"], 10188000.0)
        self.assertAlmostEqual(data["labor_ratio"], 0.340, places=3)

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

    def test_08_list_alerts_invalid_severity(self):
        res = self.client.get("/api/v1/alerts?severity=SUPER_CRITICAL")
        self.assertEqual(res.status_code, 400)

    def test_09_get_daily_dashboard_normal(self):
        res = self.client.get("/api/v1/dashboard/daily/2026-06-12")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["date"], "2026-06-12")
        self.assertEqual(data["data_status"], "OK")
        self.assertEqual(data["dataset_type"], "SYNTHETIC")
        self.assertIsNotNone(data["kpis"]["sales"])
        self.assertIsNotNone(data["kpis"]["labor_ratio"])
        
        # Verify Labor Alert is present
        rule_ids = [a["rule_id"] for a in data["alerts"]]
        self.assertIn("R-LAB-01", rule_ids)

    def test_10_get_daily_dashboard_ga007_data_incomplete(self):
        # GA-007 (2026-08-21): DATA_INCOMPLETE returns null for dependent calculations
        res = self.client.get("/api/v1/dashboard/daily/2026-08-21")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["date"], "2026-08-21")
        self.assertEqual(data["data_status"], "DATA_INCOMPLETE")
        
        # Mandatory Null for Missing dependent calculations (GP-01, GP-02)
        self.assertIsNone(data["kpis"]["food_cost"])
        self.assertIsNone(data["kpis"]["food_cost_ratio"])
        self.assertIsNone(data["kpis"]["contribution"])
        self.assertIsNone(data["kpis"]["contribution_ratio"])
        
        # R-DQ-01 Alert present
        rule_ids = [a["rule_id"] for a in data["alerts"]]
        self.assertIn("R-DQ-01", rule_ids)

    def test_11_dashboard_summary(self):
        res = self.client.get("/api/v1/dashboard/summary?start_date=2026-06-01&end_date=2026-08-31")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_days"], 92)
        self.assertEqual(data["data_complete_days"], 91)
        self.assertEqual(data["data_incomplete_days"], 1)
        self.assertGreater(data["total_sales"], 0)
        self.assertGreater(data["total_contribution"], 0)
        self.assertGreater(data["critical_alert_count"], 0)

if __name__ == '__main__':
    unittest.main()
"""

# 3. Persistence Regression Tests
files['tests/persistence/test_persistence_regression.py'] = """# -*- coding: utf-8 -*-
import json
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.database import Base
from apps.api.models.facts import DailyFact
from apps.api.models.alerts import Alert
from apps.api.services.ingestion_service import IngestionService
from domains.pipeline import run_full_pipeline

class TestPersistenceRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
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
            if res["data_status"] == "OK":
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
            else:
                self.assertIsNone(db_f.food_cost)
                self.assertIsNone(db_f.contribution)

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
\"\"\"

# 4. Reproducibility Tests
files['tests/persistence/test_reproducibility.py'] = \"\"\"# -*- coding: utf-8 -*-
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.database import Base
from apps.api.models.facts import DailyFact
from apps.api.models.alerts import Alert, PeriodAlert
from apps.api.services.ingestion_service import IngestionService

class TestReproducibility(unittest.TestCase):
    def test_identical_ingestion_across_two_independent_databases(self):
        # Verify 100% identity across two independent DBs

        # DB A
        engine_a = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine_a)
        session_a = sessionmaker(bind=engine_a)()
        service_a = IngestionService(session_a)
        service_a.ingest_synthetic_dataset("data/synthetic/damga_dataset.json", dataset_type="SYNTHETIC")
        facts_a = session_a.query(DailyFact).order_by(DailyFact.business_date.asc()).all()
        alerts_a = session_a.query(Alert).order_by(Alert.business_date.asc(), Alert.rule_id.asc()).all()
        p_alerts_a = session_a.query(PeriodAlert).order_by(PeriodAlert.target_start.asc(), PeriodAlert.rule_id.asc()).all()
        session_a.close()

        # DB B
        engine_b = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine_b)
        session_b = sessionmaker(bind=engine_b)()
        service_b = IngestionService(session_b)
        service_b.ingest_synthetic_dataset("data/synthetic/damga_dataset.json", dataset_type="SYNTHETIC")
        facts_b = session_b.query(DailyFact).order_by(DailyFact.business_date.asc()).all()
        alerts_b = session_b.query(Alert).order_by(Alert.business_date.asc(), Alert.rule_id.asc()).all()
        p_alerts_b = session_b.query(PeriodAlert).order_by(PeriodAlert.target_start.asc(), PeriodAlert.rule_id.asc()).all()
        session_b.close()

        # Compare Facts
        self.assertEqual(len(facts_a), len(facts_b))
        for fa, fb in zip(facts_a, facts_b):
            self.assertEqual(fa.business_date, fb.business_date)
            self.assertEqual(fa.sales, fb.sales)
            self.assertEqual(fa.labor_ratio, fb.labor_ratio)
            self.assertEqual(fa.food_cost_ratio, fb.food_cost_ratio)
            self.assertEqual(fa.contribution, fb.contribution)
            self.assertEqual(fa.data_status, fb.data_status)

        # Compare Alerts
        self.assertEqual(len(alerts_a), len(alerts_b))
        for aa, ab in zip(alerts_a, alerts_b):
            self.assertEqual(aa.business_date, ab.business_date)
            self.assertEqual(aa.rule_id, ab.rule_id)
            self.assertEqual(aa.severity, ab.severity)
            self.assertEqual(aa.actual_value, ab.actual_value)

        # Compare Period Alerts
        self.assertEqual(len(p_alerts_a), len(p_alerts_b))
        for pa, pb in zip(p_alerts_a, p_alerts_b):
            self.assertEqual(pa.rule_id, pb.rule_id)
            self.assertEqual(pa.target_start, pb.target_start)
            self.assertEqual(pa.target_end, pb.target_end)
            self.assertEqual(pa.target_value, pb.target_value)

if __name__ == '__main__':
    unittest.main()
"""

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

print(f"Successfully generated {len(files)} Phase 2 test suite files.")

