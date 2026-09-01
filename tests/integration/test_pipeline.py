# -*- coding: utf-8 -*-
import json
import os
import unittest
from domains.pipeline import process_daily_record, run_full_pipeline

def to_rule_engine_row_for_test(res):
    raw_date = res['raw_date']
    if res['data_status'] == 'DATA_INCOMPLETE':
        return {
            'Date': raw_date,
            'Labor_Alert': 'BLOCKED',
            'FoodCost_Alert': 'BLOCKED',
            'Inventory_Alert': 'BLOCKED',
            'Waste_Alert': 'BLOCKED',
            'Customer_Alert': 'BLOCKED',
            'Data_Quality': 'DATA_INCOMPLETE',
            'Detected_Anomaly': 'GA-007',
            'Priority': 'CRITICAL'
        }
    alerts = res.get('alerts', [])
    lab = next((a['severity'] for a in alerts if a['rule_id'] == 'R-LAB-01'), 'OK')
    fc = next((a['severity'] for a in alerts if a['rule_id'] == 'R-FC-01'), 'OK')
    inv = next((a['severity'] for a in alerts if a['rule_id'] == 'R-INV-01'), 'OK')
    wst = next((a['severity'] for a in alerts if a['rule_id'] == 'R-WST-01'), 'OK')
    cus = next((a['severity'] for a in alerts if a['rule_id'] == 'R-CUS-01'), 'OK')
    
    if any(a['severity'] == 'CRITICAL' for a in alerts): prio = 'CRITICAL'
    elif any(a['severity'] == 'HIGH' for a in alerts): prio = 'HIGH'
    elif any(a['severity'] == 'MEDIUM' for a in alerts): prio = 'MEDIUM'
    else: prio = 'NORMAL'
    
    legacy_anomaly = ''
    if lab == 'HIGH': legacy_anomaly = 'GA-001'
    elif inv == 'CRITICAL': legacy_anomaly = 'GA-002'
    elif fc == 'HIGH': legacy_anomaly = 'GA-003'
    elif wst == 'HIGH': legacy_anomaly = 'GA-004'
    elif cus == 'MEDIUM': legacy_anomaly = 'GA-006'
    
    return {
        'Date': raw_date,
        'Labor_Alert': lab,
        'FoodCost_Alert': fc,
        'Inventory_Alert': inv,
        'Waste_Alert': wst,
        'Customer_Alert': cus,
        'Data_Quality': 'OK',
        'Detected_Anomaly': legacy_anomaly,
        'Priority': prio
    }

class TestPipelineIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dataset_path = os.path.join(os.path.dirname(__file__), '../../data/synthetic/damga_dataset.json')
        if not os.path.exists(dataset_path):
            dataset_path = 'data/synthetic/damga_dataset.json'
        with open(dataset_path, 'r', encoding='utf-8') as f:
            cls.dataset = json.load(f)

        cls.header = cls.dataset['Daily_Operations'][0]
        cls.rows = [dict(zip(cls.header, r)) for r in cls.dataset['Daily_Operations'][1:]]

    def test_full_92_days_execution(self):
        """92일 전체 데이터 파이프라인 관통 및 상태 무결성 검증"""
        results = run_full_pipeline(self.rows)
        self.assertEqual(len(results), 92)

        ok_days = [r for r in results if r['data_status'] == 'OK']
        incomplete_days = [r for r in results if r['data_status'] == 'DATA_INCOMPLETE']
        self.assertEqual(len(ok_days), 91)
        self.assertEqual(len(incomplete_days), 1)

    def test_data_quality_gate_interception(self):
        """2026-08-21 (46255) 필수 식재료비 누락 차단 및 Partial Facts 보존 검증"""
        target_row = next(r for r in self.rows if r['Date'] == '46255')
        result = process_daily_record(target_row)
        
        self.assertEqual(result['data_status'], 'DATA_INCOMPLETE')
        self.assertTrue(result['blocked'])
        self.assertIsNotNone(result['facts'])
        self.assertEqual(result['facts']['sales'], 14162000.0)
        self.assertIsNone(result['facts']['food_cost'])
        self.assertIsNone(result['facts']['contribution'])
        self.assertIn('R-DQ-01', result['triggered_rule_ids'])
        self.assertIn('Food_Cost', result['missing_fields'])


    def test_facts_integrity_on_valid_days(self):
        """유효 일자의 Facts 산출 무결성 검증 (Sales, Labor Ratio, Food Cost Ratio 등)"""
        day1_row = self.rows[0] # 2026-06-01
        result = process_daily_record(day1_row)
        self.assertEqual(result['data_status'], 'OK')
        facts = result['facts']
        self.assertIsNotNone(facts)
        self.assertEqual(facts['sales'], 9202000.0)
        self.assertEqual(facts['guests'], 276)
        self.assertEqual(facts['avg_check'], round(9202000 / 276, 2))
        self.assertAlmostEqual(facts['labor_ratio'], 2335000 / 9202000)
        self.assertAlmostEqual(facts['food_cost_ratio'], 2885000 / 9202000)

    def test_excel_reference_comparison(self):
        """Excel Rule_Engine_Output 시트와의 정합성 100% 비교 검증"""
        results = run_full_pipeline(self.rows)
        ref_header = self.dataset['Rule_Engine_Output'][0]
        ref_rows = [dict(zip(ref_header, r)) for r in self.dataset['Rule_Engine_Output'][1:]]
        
        mismatches = 0
        for idx in range(len(self.rows)):
            code_out = to_rule_engine_row_for_test(results[idx])
            ref_out = ref_rows[idx]
            for col in ref_header:
                if code_out.get(col) != ref_out.get(col):
                    mismatches += 1
        self.assertEqual(mismatches, 0)

if __name__ == '__main__':
    unittest.main()


