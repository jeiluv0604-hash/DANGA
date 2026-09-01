# -*- coding: utf-8 -*-
import unittest
from domains.rules import (
    evaluate_data_quality_rule,
    evaluate_labor_rule,
    evaluate_inventory_variance_rule,
    evaluate_food_cost_rule,
    evaluate_waste_rule,
    evaluate_customer_rule,
    detect_food_cost_streak,
    detect_profit_reversal
)

class TestRuleEngine(unittest.TestCase):
    def test_r_dq_01(self):
        dq_blocked = {'blocked': True, 'missing_fields': ['Food_Cost']}
        alert = evaluate_data_quality_rule(dq_blocked)
        self.assertIsNotNone(alert)
        self.assertEqual(alert['rule_id'], 'R-DQ-01')
        self.assertEqual(alert['severity'], 'CRITICAL')
        self.assertEqual(alert['status'], 'DATA_INCOMPLETE')

        dq_ok = {'blocked': False, 'missing_fields': []}
        self.assertIsNone(evaluate_data_quality_rule(dq_ok))

    def test_r_lab_01(self):
        # 34.0% >= 33.0% -> Alert
        alert = evaluate_labor_rule(0.34)
        self.assertIsNotNone(alert)
        self.assertEqual(alert['rule_id'], 'R-LAB-01')
        self.assertEqual(alert['severity'], 'HIGH')

        # 32.5% < 33.0% -> OK
        self.assertIsNone(evaluate_labor_rule(0.325))
        self.assertIsNone(evaluate_labor_rule(None))

    def test_r_inv_01(self):
        # -6.2kg <= -5.0kg -> Alert
        alert = evaluate_inventory_variance_rule(-6.2)
        self.assertIsNotNone(alert)
        self.assertEqual(alert['rule_id'], 'R-INV-01')
        self.assertEqual(alert['severity'], 'CRITICAL')

        # -1.5kg > -5.0kg -> OK
        self.assertIsNone(evaluate_inventory_variance_rule(-1.5))
        self.assertIsNone(evaluate_inventory_variance_rule(0.5))

    def test_r_fc_01(self):
        # 40.0% >= 39.0% -> Alert
        alert = evaluate_food_cost_rule(0.40)
        self.assertIsNotNone(alert)
        self.assertEqual(alert['rule_id'], 'R-FC-01')
        self.assertEqual(alert['severity'], 'HIGH')

        # 33.0% < 39.0% -> OK
        self.assertIsNone(evaluate_food_cost_rule(0.33))

    def test_r_wst_01(self):
        # 5.5% >= 5.0% -> Alert
        alert = evaluate_waste_rule(0.055)
        self.assertIsNotNone(alert)
        self.assertEqual(alert['rule_id'], 'R-WST-01')
        self.assertEqual(alert['severity'], 'HIGH')

        # 2.0% < 5.0% -> OK
        self.assertIsNone(evaluate_waste_rule(0.02))

    def test_r_cus_01(self):
        # Complaints=8, Rating=4.08 -> Alert
        alert = evaluate_customer_rule(8, 4.08)
        self.assertIsNotNone(alert)
        self.assertEqual(alert['rule_id'], 'R-CUS-01')
        self.assertEqual(alert['severity'], 'MEDIUM')

        # Complaints=2, Rating=4.6 -> OK
        self.assertIsNone(evaluate_customer_rule(2, 4.6))

    def test_r_pro_01_generalization(self):
        # Rolling window test
        records = []
        for i in range(14):
            date_str = f"2026-11-{i+1:02d}"
            if i < 7: # baseline
                records.append({'date': date_str, 'facts': {'sales': 10000000.0, 'contribution': 4000000.0}}) # 40%
            else: # target: sales up, contrib down
                records.append({'date': date_str, 'facts': {'sales': 12000000.0, 'contribution': 3600000.0}}) # 30%
                
        alerts = detect_profit_reversal(records, window_days=7)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['rule_id'], 'R-PRO-01')
        self.assertEqual(alerts[0]['severity'], 'HIGH')

    def test_r_fc_period_rule_generalization(self):
        records = [
            {'date': f'2026-11-{i+1:02d}', 'facts': {'food_cost_ratio': 0.395}} for i in range(7)
        ]
        alerts = detect_food_cost_streak(records, threshold=0.39, min_consecutive_days=7)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['rule_id'], 'R-FC-01-PERIOD')
        self.assertEqual(alerts[0]['consecutive_days'], 7)

if __name__ == '__main__':
    unittest.main()


