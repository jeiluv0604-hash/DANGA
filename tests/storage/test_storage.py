# -*- coding: utf-8 -*-
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
        self.assertEqual(dq_fact.sales, 14162000.0)
        self.assertEqual(dq_fact.guests, 419)
        self.assertEqual(dq_fact.labor_cost, 3470000.0)
        self.assertAlmostEqual(dq_fact.labor_ratio, 0.24502, places=3)
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
