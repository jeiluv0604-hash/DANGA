# -*- coding: utf-8 -*-
import unittest
from domains.rules import (
    evaluate_labor_rule,
    evaluate_inventory_variance_rule,
    evaluate_food_cost_rule,
    evaluate_waste_rule,
    evaluate_customer_rule
)

class TestMutationBoundaries(unittest.TestCase):
    def test_labor_ratio_boundary(self):
        # 0.329999 -> OK
        self.assertIsNone(evaluate_labor_rule(0.329999))
        # 0.330000 -> ALERT
        res = evaluate_labor_rule(0.330000)
        self.assertIsNotNone(res)
        self.assertEqual(res['rule_id'], 'R-LAB-01')
        self.assertEqual(res['severity'], 'HIGH')

    def test_inventory_variance_boundary(self):
        # -4.999 -> OK
        self.assertIsNone(evaluate_inventory_variance_rule(-4.999))
        # -5.000 -> ALERT
        res = evaluate_inventory_variance_rule(-5.000)
        self.assertIsNotNone(res)
        self.assertEqual(res['rule_id'], 'R-INV-01')
        self.assertEqual(res['severity'], 'CRITICAL')

    def test_food_cost_ratio_boundary(self):
        # 0.389999 -> OK
        self.assertIsNone(evaluate_food_cost_rule(0.389999))
        # 0.390000 -> ALERT
        res = evaluate_food_cost_rule(0.390000)
        self.assertIsNotNone(res)
        self.assertEqual(res['rule_id'], 'R-FC-01')
        self.assertEqual(res['severity'], 'HIGH')

    def test_waste_ratio_boundary(self):
        # 0.049999 -> OK
        self.assertIsNone(evaluate_waste_rule(0.049999))
        # 0.050000 -> ALERT
        res = evaluate_waste_rule(0.050000)
        self.assertIsNotNone(res)
        self.assertEqual(res['rule_id'], 'R-WST-01')
        self.assertEqual(res['severity'], 'HIGH')

    def test_customer_complaints_boundary(self):
        # Complaints = 4, Rating = 4.5 -> OK
        self.assertIsNone(evaluate_customer_rule(complaints=4, rating=4.5))
        # Complaints = 5, Rating = 4.5 -> ALERT
        res = evaluate_customer_rule(complaints=5, rating=4.5)
        self.assertIsNotNone(res)
        self.assertEqual(res['rule_id'], 'R-CUS-01')

    def test_customer_rating_boundary(self):
        # Rating = 4.20, Complaints = 0 -> OK
        self.assertIsNone(evaluate_customer_rule(complaints=0, rating=4.20))
        # Rating = 4.199, Complaints = 0 -> ALERT
        res = evaluate_customer_rule(complaints=0, rating=4.199)
        self.assertIsNotNone(res)
        self.assertEqual(res['rule_id'], 'R-CUS-01')

if __name__ == '__main__':
    unittest.main()

