# -*- coding: utf-8 -*-
import json
import os
import unittest
from domains.pipeline import process_daily_record, run_full_pipeline
from domains.rules import detect_food_cost_streak, detect_profit_reversal

# Test Harness Rule -> Golden Scenario Ground Truth Mapping
RULE_TO_GOLDEN_MAP = {
    'R-LAB-01': 'GA-001',
    'R-INV-01': 'GA-002',
    'R-FC-01': 'GA-003',
    'R-FC-01-PERIOD': 'GA-003',
    'R-WST-01': 'GA-004',
    'R-PRO-01': 'GA-005',
    'R-CUS-01': 'GA-006',
    'R-DQ-01': 'GA-007'
}

class TestRealGoldenHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dataset_path = os.path.join(os.path.dirname(__file__), '../../data/synthetic/damga_dataset.json')
        if not os.path.exists(dataset_path):
            dataset_path = 'data/synthetic/damga_dataset.json'
        with open(dataset_path, 'r', encoding='utf-8') as f:
            cls.dataset = json.load(f)

        cls.header = cls.dataset['Daily_Operations'][0]
        # Important: row dict without Expected_Anomaly_ID passed to detection
        cls.raw_rows = [dict(zip(cls.header, r)) for r in cls.dataset['Daily_Operations'][1:]]
        cls.pipeline_results = run_full_pipeline(cls.raw_rows)
        cls.results_by_serial = {r['raw_date']: r for r in cls.pipeline_results}

    def test_ht001_ga001_labor_anomaly(self):
        """HT-001 / GA-001 (2026-06-12): 금요일 비피크 과잉 인력 투입 탐지"""
        res = self.results_by_serial['46185']
        self.assertEqual(res['date'], '2026-06-12')
        self.assertIn('R-LAB-01', res['triggered_rule_ids'])
        
        lab_alerts = [a for a in res['alerts'] if a['rule_id'] == 'R-LAB-01']
        self.assertEqual(len(lab_alerts), 1)
        alert = lab_alerts[0]
        self.assertEqual(alert['severity'], 'HIGH')
        self.assertGreaterEqual(alert['actual'], 0.33)
        self.assertEqual(RULE_TO_GOLDEN_MAP[alert['rule_id']], 'GA-001')

    def test_ht002_ga002_inventory_variance_anomaly(self):
        """HT-002 / GA-002 (2026-06-24): 육류 실재고 부족(-6.2kg) 탐지 & 안전 표현 검증"""
        res = self.results_by_serial['46197']
        self.assertEqual(res['date'], '2026-06-24')
        self.assertIn('R-INV-01', res['triggered_rule_ids'])
        
        inv_alerts = [a for a in res['alerts'] if a['rule_id'] == 'R-INV-01']
        self.assertEqual(len(inv_alerts), 1)
        alert = inv_alerts[0]
        self.assertEqual(alert['severity'], 'CRITICAL')
        self.assertLessEqual(alert['actual'], -5.0)
        self.assertEqual(RULE_TO_GOLDEN_MAP[alert['rule_id']], 'GA-002')
        
        # GP-05 No Accusation: 부정행위/절도/횡령 단정 단어 금지 검증
        prohibited_words = ['절도', '횡령', '도난', '범죄', '과실', 'theft', 'fraud']
        alert_str = json.dumps(alert, ensure_ascii=False)
        for w in prohibited_words:
            self.assertNotIn(w, alert_str.lower())

    def test_ht003_ga003_food_cost_period_anomaly(self):
        """HT-003 / GA-003 (2026-07-07 ~ 2026-07-13): 7일 연속 한우 원가 압박 일반화 탐지"""
        period_serials = [str(s) for s in range(46210, 46217)]
        period_results = [self.results_by_serial[s] for s in period_serials]
        
        # 일별 R-FC-01 발생 확인
        for r in period_results:
            self.assertIn('R-FC-01', r['triggered_rule_ids'])
            
        # 일반 streak detector로 7일 연속 급등 탐지 검증
        streaks = detect_food_cost_streak(self.pipeline_results, threshold=0.39, min_consecutive_days=7)
        self.assertEqual(len(streaks), 1)
        streak = streaks[0]
        self.assertEqual(streak['start_date'], '2026-07-07')
        self.assertEqual(streak['end_date'], '2026-07-13')
        self.assertEqual(streak['consecutive_days'], 7)
        self.assertEqual(RULE_TO_GOLDEN_MAP[streak['rule_id']], 'GA-003')

    def test_ht004_ga004_waste_anomaly(self):
        """HT-004 / GA-004 (2026-07-18): 폐기량 급증(>=5%) 탐지"""
        res = self.results_by_serial['46221']
        self.assertEqual(res['date'], '2026-07-18')
        self.assertIn('R-WST-01', res['triggered_rule_ids'])
        
        wst_alerts = [a for a in res['alerts'] if a['rule_id'] == 'R-WST-01']
        self.assertEqual(len(wst_alerts), 1)
        alert = wst_alerts[0]
        self.assertEqual(alert['severity'], 'HIGH')
        self.assertGreaterEqual(alert['actual'], 0.05)
        self.assertEqual(RULE_TO_GOLDEN_MAP[alert['rule_id']], 'GA-004')

    def test_ht005_ga005_profit_reversal_anomaly(self):
        """HT-005 / GA-005 (2026-08-01 ~ 2026-08-07): 매출 증가 대비 공헌이익 역행 악화 일반화 탐지"""
        reversals = detect_profit_reversal(self.pipeline_results, window_days=7)
        matching = [r for r in reversals if r['target_start'] == '2026-08-01' and r['target_end'] == '2026-08-07']
        self.assertEqual(len(matching), 1)
        rev = matching[0]
        self.assertEqual(rev['rule_id'], 'R-PRO-01')
        self.assertEqual(rev['severity'], 'HIGH')
        self.assertGreater(rev['actual']['target_sales'], rev['actual']['baseline_sales'])
        self.assertLess(rev['actual']['target_contribution_ratio'], rev['actual']['baseline_contribution_ratio'])
        self.assertEqual(RULE_TO_GOLDEN_MAP[rev['rule_id']], 'GA-005')

    def test_ht006_ga006_customer_voc_anomaly(self):
        """HT-006 / GA-006 (2026-08-15): 클레임 8건 & 평점 4.08 악화 동시 탐지"""
        res = self.results_by_serial['46249']
        self.assertEqual(res['date'], '2026-08-15')
        self.assertIn('R-CUS-01', res['triggered_rule_ids'])
        
        cus_alerts = [a for a in res['alerts'] if a['rule_id'] == 'R-CUS-01']
        self.assertEqual(len(cus_alerts), 1)
        alert = cus_alerts[0]
        self.assertEqual(alert['severity'], 'MEDIUM')
        self.assertGreaterEqual(alert['actual']['complaints'], 5)
        self.assertLess(alert['actual']['rating'], 4.2)
        self.assertEqual(RULE_TO_GOLDEN_MAP[alert['rule_id']], 'GA-006')

    def test_ht007_ga007_data_quality_gate(self):
        """HT-007 / GA-007 (2026-08-21): 식재료비 누락 시 DATA_INCOMPLETE 차단 & 독립 Facts 보존 및 종속 Facts Null 검증"""
        res = self.results_by_serial['46255']
        self.assertEqual(res['date'], '2026-08-21')
        self.assertEqual(res['data_status'], 'DATA_INCOMPLETE')
        self.assertTrue(res['blocked'])
        self.assertFalse(res['ai_eligible'])
        
        # Independent facts preserved (Phase 2.1)
        facts = res['facts']
        self.assertIsNotNone(facts)
        self.assertEqual(facts['sales'], 14162000.0)
        self.assertEqual(facts['guests'], 419)
        self.assertEqual(facts['labor_cost'], 3470000.0)

        
        # Dependent facts on Food_Cost are None
        self.assertIsNone(facts['food_cost'])
        self.assertIsNone(facts['food_cost_ratio'])
        self.assertIsNone(facts['contribution'])
        self.assertIsNone(facts['contribution_ratio'])

        self.assertIn('R-DQ-01', res['triggered_rule_ids'])
        self.assertIn('Food_Cost', res['missing_fields'])
        self.assertEqual(RULE_TO_GOLDEN_MAP['R-DQ-01'], 'GA-007')

if __name__ == '__main__':
    unittest.main()



