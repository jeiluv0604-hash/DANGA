# -*- coding: utf-8 -*-
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
