# -*- coding: utf-8 -*-
import unittest
from domains.data_quality.gate import validate_required_fields
from domains.customer.facts import calculate_complaints, calculate_review_count, calculate_daily_rating
from domains.sales.facts import calculate_sales, calculate_guests
from domains.labor.facts import calculate_labor_cost

class TestInvalidInputs(unittest.TestCase):
    def get_valid_record(self):
        return {
            'Date': '2026-10-01',
            'Sales': 10000000.0,
            'Guests': 300,
            'Labor_Cost': 2700000.0,
            'Food_Cost': 3250000.0,
            'Incoming_kg': 150.0,
            'Sold_kg': 140.0,
            'Waste_kg': 1.4,
            'Actual_End_kg': 24.5,
            'Rating': 4.65,
            'Review_Count': 12,
            'Complaints': 1
        }

    def test_negative_sales_blocked(self):
        rec = self.get_valid_record()
        rec['Sales'] = -1
        ok, res = validate_required_fields(rec)
        self.assertFalse(ok)
        self.assertTrue(res['blocked'])
        self.assertIn('Sales', res['missing_fields'])

    def test_string_sales_blocked(self):
        rec = self.get_valid_record()
        rec['Sales'] = 'ABC'
        ok, res = validate_required_fields(rec)
        self.assertFalse(ok)
        self.assertTrue(res['blocked'])

    def test_negative_guests_blocked(self):
        rec = self.get_valid_record()
        rec['Guests'] = -1
        ok, res = validate_required_fields(rec)
        self.assertFalse(ok)
        self.assertTrue(res['blocked'])

    def test_string_guests_blocked(self):
        rec = self.get_valid_record()
        rec['Guests'] = 'ten'
        ok, res = validate_required_fields(rec)
        self.assertFalse(ok)
        self.assertTrue(res['blocked'])

    def test_negative_labor_cost_blocked(self):
        rec = self.get_valid_record()
        rec['Labor_Cost'] = -100
        ok, res = validate_required_fields(rec)
        self.assertFalse(ok)
        self.assertTrue(res['blocked'])

    def test_empty_food_cost_blocked(self):
        rec = self.get_valid_record()
        rec['Food_Cost'] = ''
        ok, res = validate_required_fields(rec)
        self.assertFalse(ok)
        self.assertTrue(res['blocked'])

    def test_unknown_food_cost_blocked(self):
        rec = self.get_valid_record()
        rec['Food_Cost'] = 'unknown'
        ok, res = validate_required_fields(rec)
        self.assertFalse(ok)
        self.assertTrue(res['blocked'])

    def test_negative_waste_kg_blocked(self):
        rec = self.get_valid_record()
        rec['Waste_kg'] = -1
        ok, res = validate_required_fields(rec)
        self.assertFalse(ok)
        self.assertTrue(res['blocked'])

    def test_rating_out_of_bounds_blocked(self):
        rec = self.get_valid_record()
        rec['Rating'] = 5.5
        ok, res = validate_required_fields(rec)
        self.assertFalse(ok)
        self.assertTrue(res['blocked'])

        rec['Rating'] = -1
        ok2, res2 = validate_required_fields(rec)
        self.assertFalse(ok2)
        self.assertTrue(res2['blocked'])

    def test_negative_complaints_blocked(self):
        rec = self.get_valid_record()
        rec['Complaints'] = -2
        ok, res = validate_required_fields(rec)
        self.assertFalse(ok)
        self.assertTrue(res['blocked'])

    def test_invalid_actual_end_kg_blocked(self):
        rec = self.get_valid_record()
        rec['Actual_End_kg'] = 'missing'
        ok, res = validate_required_fields(rec)
        self.assertFalse(ok)
        self.assertTrue(res['blocked'])

    def test_optional_customer_fields_missing_returns_none(self):
        """Missing vs Zero 분리 검증: Complaints/Review/Rating이 누락 시 0이 아닌 None 반환"""
        self.assertIsNone(calculate_complaints(None))
        self.assertIsNone(calculate_complaints(''))
        self.assertEqual(calculate_complaints(0), 0)

        self.assertIsNone(calculate_review_count(None))
        self.assertIsNone(calculate_review_count(''))
        self.assertEqual(calculate_review_count(0), 0)

        self.assertIsNone(calculate_daily_rating(None))
        self.assertIsNone(calculate_daily_rating(''))
        self.assertEqual(calculate_daily_rating(0), 0.0)

if __name__ == '__main__':
    unittest.main()

