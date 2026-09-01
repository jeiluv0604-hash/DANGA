# -*- coding: utf-8 -*-
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.database import Base
from apps.api.models.facts import DailyFact
from apps.api.models.alerts import Alert, PeriodAlert
from apps.api.services.ingestion_service import IngestionService

class TestReproducibility(unittest.TestCase):
    def test_identical_ingestion_across_two_independent_databases(self):
        # DB A
        engine_a = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(bind=engine_a)
        session_a = sessionmaker(bind=engine_a)()
        service_a = IngestionService(session_a)
        service_a.ingest_synthetic_dataset('data/synthetic/damga_dataset.json', dataset_type='SYNTHETIC')
        facts_a = session_a.query(DailyFact).order_by(DailyFact.business_date.asc()).all()
        alerts_a = session_a.query(Alert).order_by(Alert.business_date.asc(), Alert.rule_id.asc()).all()
        p_alerts_a = session_a.query(PeriodAlert).order_by(PeriodAlert.target_start.asc(), PeriodAlert.rule_id.asc()).all()
        session_a.close()

        # DB B
        engine_b = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(bind=engine_b)
        session_b = sessionmaker(bind=engine_b)()
        service_b = IngestionService(session_b)
        service_b.ingest_synthetic_dataset('data/synthetic/damga_dataset.json', dataset_type='SYNTHETIC')
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
