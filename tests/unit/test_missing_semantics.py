# -*- coding: utf-8 -*-
import unittest
from domains.pipeline import process_daily_record
from domains.customer.facts import calculate_daily_rating, calculate_complaints, calculate_review_count

class TestMissingSemantics(unittest.TestCase):
    def test_data01_service_kg_zero_is_available(self):
        # DATA-01: Service_kg = 0 -> AVAILABLE, value: 0.0
        row = {
            'Date': '46200',
            'Sales': 10000000,
            'Guests': 200,
            'Labor_Cost': 2500000,
            'Food_Cost': 3000000,
            'Incoming_kg': 100,
            'Sold_kg': 80,
            'Service_kg': 0,
            'Waste_kg': 2,
            'Actual_End_kg': 18
        }
        res = process_daily_record(row)
        self.assertEqual(res['facts']['service_kg'], 0.0)
        self.assertEqual(res['facts']['kpi_status']['service_kg'], 'AVAILABLE')
        self.assertEqual(res['facts']['theory_end_kg'], 18.0)
        self.assertEqual(res['facts']['variance_kg'], 0.0)

    def test_data02_service_kg_none_blocks_theory_end_when_not_provided(self):
        # DATA-02: Service_kg = None and Theory_End_kg = None -> Theory End & Variance blocked
        row = {
            'Date': '46200',
            'Sales': 10000000,
            'Guests': 200,
            'Labor_Cost': 2500000,
            'Food_Cost': 3000000,
            'Incoming_kg': 100,
            'Sold_kg': 80,
            'Service_kg': None,
            'Waste_kg': 2,
            'Actual_End_kg': 18
        }
        res = process_daily_record(row)
        self.assertIsNone(res['facts']['service_kg'])
        self.assertEqual(res['facts']['kpi_status']['service_kg'], 'NOT_PROVIDED')
        self.assertIsNone(res['facts']['theory_end_kg'])
        self.assertIsNone(res['facts']['variance_kg'])
        self.assertEqual(res['facts']['kpi_status']['theory_end_kg'], 'BLOCKED_DEPENDENCY')
        self.assertEqual(res['facts']['kpi_status']['inventory_variance'], 'BLOCKED_DEPENDENCY')

    def test_data03_service_kg_none_with_provided_theory_end(self):
        # DATA-03: Service_kg = None but Theory_End_kg provided -> Variance calculable
        row = {
            'Date': '46200',
            'Sales': 10000000,
            'Guests': 200,
            'Labor_Cost': 2500000,
            'Food_Cost': 3000000,
            'Incoming_kg': 100,
            'Sold_kg': 80,
            'Service_kg': None,
            'Waste_kg': 2,
            'Actual_End_kg': 18,
            'Theory_End_kg': 19.5
        }
        res = process_daily_record(row)
        self.assertIsNone(res['facts']['service_kg'])
        self.assertEqual(res['facts']['kpi_status']['service_kg'], 'NOT_PROVIDED')
        self.assertEqual(res['facts']['theory_end_kg'], 19.5)
        self.assertEqual(res['facts']['variance_kg'], -1.5)
        self.assertEqual(res['facts']['kpi_status']['theory_end_kg'], 'AVAILABLE')
        self.assertEqual(res['facts']['kpi_status']['inventory_variance'], 'AVAILABLE')

    def test_data04_complaints_none_distinct_from_zero(self):
        # DATA-04: Complaints None != 0
        self.assertIsNone(calculate_complaints(None))
        self.assertIsNone(calculate_complaints(''))
        self.assertEqual(calculate_complaints(0), 0)
        self.assertEqual(calculate_complaints('0'), 0)

    def test_data05_review_count_none_distinct_from_zero(self):
        # DATA-05: Review_Count None != 0
        self.assertIsNone(calculate_review_count(None))
        self.assertIsNone(calculate_review_count(''))
        self.assertEqual(calculate_review_count(0), 0)
        self.assertEqual(calculate_review_count('0'), 0)

    def test_data06_rating_none_distinct_from_zero(self):
        # DATA-06: Rating None != 0.0
        self.assertIsNone(calculate_daily_rating(None))
        self.assertIsNone(calculate_daily_rating(''))
        self.assertEqual(calculate_daily_rating(0.0), 0.0)
        self.assertEqual(calculate_daily_rating('4.5'), 4.5)

if __name__ == '__main__':
    unittest.main()
