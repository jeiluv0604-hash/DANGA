# -*- coding: utf-8 -*-
import json
import os
import unittest
from domains.pipeline import process_daily_record, run_full_pipeline
from domains.rules import detect_food_cost_streak, detect_profit_reversal

class TestAdversarialGeneralization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        adv_path = os.path.join(os.path.dirname(__file__), '../../data/fixtures/adversarial/adversarial_dataset.json')
        with open(adv_path, 'r', encoding='utf-8') as f:
            cls.dataset = json.load(f)

        header = cls.dataset['Daily_Operations'][0]
        cls.raw_rows = [dict(zip(header, r)) for r in cls.dataset['Daily_Operations'][1:]]
        cls.pipeline_results = run_full_pipeline(cls.raw_rows)
        cls.results_by_date = {r['date']: r for r in cls.pipeline_results}

    def test_adv001_labor_anomaly(self):
        """ADV-001 (2026-10-15): 임의의 다른 날짜에서 인건비율 이상(R-LAB-01) 자동 탐지 검증"""
        res = self.results_by_date['2026-10-15']
        self.assertEqual(res['data_status'], 'OK')
        self.assertIn('R-LAB-01', res['triggered_rule_ids'])
        alert = next(a for a in res['alerts'] if a['rule_id'] == 'R-LAB-01')
        self.assertEqual(alert['severity'], 'HIGH')
        self.assertGreaterEqual(alert['actual'], 0.33)

    def test_adv002_inventory_variance(self):
        """ADV-002 (2026-10-22): 임의의 다른 날짜에서 재고 불일치 -7.2kg (R-INV-01) 자동 탐지 검증"""
        res = self.results_by_date['2026-10-22']
        self.assertEqual(res['data_status'], 'OK')
        self.assertIn('R-INV-01', res['triggered_rule_ids'])
        alert = next(a for a in res['alerts'] if a['rule_id'] == 'R-INV-01')
        self.assertEqual(alert['severity'], 'CRITICAL')
        self.assertLessEqual(alert['actual'], -5.0)

    def test_adv003_food_cost_streak(self):
        """ADV-003 (2026-11-01 ~ 2026-11-07): 임의의 다른 7일 구간에서 원가율 40% 연속 급등(R-FC-01-PERIOD) 자동 탐지"""
        streaks = detect_food_cost_streak(self.pipeline_results, threshold=0.39, min_consecutive_days=7)
        self.assertEqual(len(streaks), 1)
        streak = streaks[0]
        self.assertEqual(streak['start_date'], '2026-11-01')
        self.assertEqual(streak['end_date'], '2026-11-07')
        self.assertEqual(streak['consecutive_days'], 7)
        self.assertEqual(streak['severity'], 'HIGH')

    def test_adv004_waste_anomaly(self):
        """ADV-004 (2026-11-15): 임의의 다른 날짜에서 폐기율 6.2% (R-WST-01) 자동 탐지 검증"""
        res = self.results_by_date['2026-11-15']
        self.assertEqual(res['data_status'], 'OK')
        self.assertIn('R-WST-01', res['triggered_rule_ids'])
        alert = next(a for a in res['alerts'] if a['rule_id'] == 'R-WST-01')
        self.assertEqual(alert['severity'], 'HIGH')
        self.assertGreaterEqual(alert['actual'], 0.05)

    def test_adv005_profit_reversal(self):
        """ADV-005 (2026-11-20 ~ 2026-11-26): 임의의 다른 7일 구간에서 매출 증가 대비 공헌이익 역행(R-PRO-01) 자동 탐지"""
        reversals = detect_profit_reversal(self.pipeline_results, window_days=7)
        matching = [r for r in reversals if r['target_start'] == '2026-11-20' and r['target_end'] == '2026-11-26']
        self.assertEqual(len(matching), 1)
        rev = matching[0]
        self.assertEqual(rev['rule_id'], 'R-PRO-01')
        self.assertEqual(rev['severity'], 'HIGH')
        self.assertGreater(rev['actual']['target_sales'], rev['actual']['baseline_sales'])
        self.assertLess(rev['actual']['target_contribution_ratio'], rev['actual']['baseline_contribution_ratio'])

    def test_adv006_customer_voc(self):
        """ADV-006 (2026-12-05): 임의의 다른 날짜에서 평점 4.10, 클레임 6건 (R-CUS-01) 자동 탐지 검증"""
        res = self.results_by_date['2026-12-05']
        self.assertEqual(res['data_status'], 'OK')
        self.assertIn('R-CUS-01', res['triggered_rule_ids'])
        alert = next(a for a in res['alerts'] if a['rule_id'] == 'R-CUS-01')
        self.assertEqual(alert['severity'], 'MEDIUM')

    def test_adv007_data_quality_gate(self):
        """ADV-007 (2026-12-10): 임의의 다른 날짜에서 Food_Cost 결측 시 DATA_INCOMPLETE 즉시 차단 및 Partial Facts 보존 검증"""
        res = self.results_by_date['2026-12-10']
        self.assertEqual(res['data_status'], 'DATA_INCOMPLETE')
        self.assertTrue(res['blocked'])
        self.assertFalse(res['ai_eligible'])
        self.assertIsNotNone(res['facts'])
        self.assertIsNone(res['facts']['food_cost'])
        self.assertIsNone(res['facts']['food_cost_ratio'])
        self.assertIsNone(res['facts']['contribution'])
        self.assertIn('R-DQ-01', res['triggered_rule_ids'])
        self.assertIn('Food_Cost', res['missing_fields'])

if __name__ == '__main__':
    unittest.main()


