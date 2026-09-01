# -*- coding: utf-8 -*-
import unittest
from domains.sales.facts import calculate_sales, calculate_guests, calculate_avg_check
from domains.labor.facts import calculate_labor_cost, calculate_labor_ratio
from domains.food_cost.facts import calculate_food_cost, calculate_food_cost_ratio
from domains.inventory.facts import calculate_theory_end, calculate_inventory_variance, calculate_waste_ratio
from domains.customer.facts import calculate_daily_rating, calculate_complaints, calculate_review_count
from domains.management.facts import calculate_contribution, calculate_contribution_ratio

class TestFactsEngine(unittest.TestCase):
    def test_sales_and_guests(self):
        self.assertEqual(calculate_sales(1000000), 1000000.0)
        self.assertEqual(calculate_sales('500000'), 500000.0)
        with self.assertRaises(ValueError):
            calculate_sales(-100)
        with self.assertRaises(ValueError):
            calculate_sales(None)

        self.assertEqual(calculate_guests(50), 50)
        self.assertEqual(calculate_guests('120'), 120)
        with self.assertRaises(ValueError):
            calculate_guests(-5)

    def test_avg_check(self):
        self.assertEqual(calculate_avg_check(1000000, 50), 20000.0)
        self.assertIsNone(calculate_avg_check(1000000, 0))
        self.assertIsNone(calculate_avg_check(1000000, -10))
        self.assertIsNone(calculate_avg_check(None, 50))

    def test_labor_ratio(self):
        self.assertEqual(calculate_labor_cost(2700000), 2700000.0)
        self.assertAlmostEqual(calculate_labor_ratio(2700000, 10000000), 0.27)
        self.assertIsNone(calculate_labor_ratio(2700000, 0))
        self.assertIsNone(calculate_labor_ratio(None, 10000000))

    def test_food_cost_ratio(self):
        self.assertEqual(calculate_food_cost(3250000), 3250000.0)
        self.assertAlmostEqual(calculate_food_cost_ratio(3250000, 10000000), 0.325)
        self.assertIsNone(calculate_food_cost_ratio(3250000, 0))
        self.assertIsNone(calculate_food_cost_ratio(None, 10000000))

    def test_inventory_calculations(self):
        # prev 10.0 + inc 100.0 - (sold 80.0 + svc 2.0 + waste 1.0) = 27.0
        theory = calculate_theory_end(10.0, 100.0, 80.0, 2.0, 1.0)
        self.assertEqual(theory, 27.0)
        
        # actual 20.8 - theory 27.0 = -6.2
        var = calculate_inventory_variance(20.8, 27.0)
        self.assertEqual(var, -6.2)

        # waste 5.0 / sold 100.0 = 0.05
        w_ratio = calculate_waste_ratio(5.0, 100.0)
        self.assertAlmostEqual(w_ratio, 0.05)
        self.assertIsNone(calculate_waste_ratio(5.0, 0))

    def test_customer_facts(self):
        self.assertEqual(calculate_daily_rating(4.55), 4.55)
        self.assertIsNone(calculate_daily_rating(''))
        with self.assertRaises(ValueError):
            calculate_daily_rating(5.5)

        self.assertEqual(calculate_complaints('3'), 3)
        self.assertEqual(calculate_review_count(10), 10)

    def test_management_facts(self):
        # 1000 - 325 - 270 = 405
        contrib = calculate_contribution(10000000, 3250000, 2700000)
        self.assertEqual(contrib, 4050000.0)
        self.assertAlmostEqual(calculate_contribution_ratio(contrib, 10000000), 0.405)
        self.assertIsNone(calculate_contribution(None, 3250000, 2700000))
        self.assertIsNone(calculate_contribution_ratio(4050000, 0))

    def test_determinism(self):
        """동일 입력 반복 실행 시 100% 동일 출력 검증 (GP-06)"""
        for _ in range(10):
            self.assertEqual(calculate_avg_check(9202000, 276), round(9202000 / 276, 2))
            self.assertEqual(calculate_labor_ratio(2335000, 9202000), 2335000 / 9202000)

if __name__ == '__main__':
    unittest.main()

