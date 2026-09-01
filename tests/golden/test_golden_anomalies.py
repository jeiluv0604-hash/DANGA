# -*- coding: utf-8 -*-
import json
import os
import unittest
from datetime import datetime, timedelta

def excel_date_to_str(serial):
    try:
        val = float(serial)
        base = datetime(1899, 12, 30)
        dt = base + timedelta(days=val)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return str(serial)

class TestGoldenDatasetV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dataset_path = os.path.join(os.path.dirname(__file__), '../../data/synthetic/damga_dataset.json')
        if not os.path.exists(dataset_path):
            dataset_path = 'data/synthetic/damga_dataset.json'
        with open(dataset_path, 'r', encoding='utf-8') as f:
            cls.dataset = json.load(f)

    def test_01_assumptions_loaded(self):
        """검증: 경영 기준 Assumptions 데이터 적재 및 무결성"""
        assumptions = self.dataset.get('Assumptions', [])
        self.assertGreater(len(assumptions), 5)
        kpi_map = {row[0]: row[1] for row in assumptions[1:] if len(row) >= 2}
        self.assertEqual(kpi_map.get('연매출 기준'), '4200000000')
        self.assertEqual(kpi_map.get('직원 재직 Pool'), '65')
        self.assertEqual(kpi_map.get('정상 인건비율 기준'), '0.27')
        self.assertEqual(kpi_map.get('정상 식재료 원가율 기준'), '0.325')

    def test_02_daily_operations_row_count(self):
        """검증: 92일간의 Daily Operations 데이터 무결성"""
        ops = self.dataset.get('Daily_Operations', [])
        # 1 header + 92 daily records = 93 rows
        self.assertEqual(len(ops), 93, '92일치 운영 데이터가 정확히 존재해야 합니다.')

    def test_03_golden_anomalies_ground_truth(self):
        """검증: GA-001 ~ GA-007 7대 골든 이상 징후 Ground Truth 정의 검증"""
        anomalies = self.dataset.get('Golden_Anomalies', [])
        self.assertGreaterEqual(len(anomalies), 8)
        anomaly_ids = [row[0] for row in anomalies[1:] if len(row) > 0]
        expected_ids = ['GA-001', 'GA-002', 'GA-003', 'GA-004', 'GA-005', 'GA-006', 'GA-007']
        for aid in expected_ids:
            self.assertIn(aid, anomaly_ids, f'{aid} 골든 이상 시나리오가 존재해야 합니다.')

    def test_04_harness_tests_mapping(self):
        """검증: HT-001 ~ HT-007 테스트 하네스 매핑 검증"""
        harness = self.dataset.get('Harness_Tests', [])
        self.assertGreaterEqual(len(harness), 8)
        test_ids = [row[0] for row in harness[1:] if len(row) > 0]
        for i in range(1, 8):
            tid = f'HT-{i:03d}'
            self.assertIn(tid, test_ids, f'{tid} 하네스 테스트 정의가 존재해야 합니다.')

    def test_05_ga007_data_quality_gate(self):
        """검증: GA-007 필수 데이터 누락에 대한 DATA_INCOMPLETE 차단 여부"""
        ops = self.dataset.get('Daily_Operations', [])
        header = ops[0]
        status_idx = header.index('Data_Status')
        fc_idx = header.index('Food_Cost')
        
        incomplete_rows = [r for r in ops[1:] if r[status_idx] == 'DATA_INCOMPLETE']
        self.assertEqual(len(incomplete_rows), 1, 'GA-007 시나리오에 해당하는 1건의 DATA_INCOMPLETE가 존재해야 합니다.')
        incomplete_row = incomplete_rows[0]
        self.assertEqual(incomplete_row[fc_idx], '', '식재료비가 누락(NULL)되어 있어야 합니다.')

if __name__ == '__main__':
    unittest.main()

