# -*- coding: utf-8 -*-
import unittest
from domains.data_quality.gate import validate_required_fields, is_empty_or_invalid

class TestDataQualityGate(unittest.TestCase):
    def test_is_empty_or_invalid(self):
        self.assertTrue(is_empty_or_invalid(None))
        self.assertTrue(is_empty_or_invalid(''))
        self.assertTrue(is_empty_or_invalid('   '))
        self.assertTrue(is_empty_or_invalid('NULL'))
        self.assertTrue(is_empty_or_invalid('none'))
        self.assertTrue(is_empty_or_invalid(float('nan')))
        self.assertFalse(is_empty_or_invalid(0))
        self.assertFalse(is_empty_or_invalid(0.0))
        self.assertFalse(is_empty_or_invalid('12345'))

    def test_validate_valid_record(self):
        valid_rec = {
            'Date': '46174',
            'Sales': 9202000,
            'Guests': 276,
            'Labor_Cost': 2335000,
            'Food_Cost': 2885000,
            'Incoming_kg': 149.5,
            'Sold_kg': 139.3,
            'Waste_kg': 1.1,
            'Actual_End_kg': 6.6
        }
        is_valid, res = validate_required_fields(valid_rec)
        self.assertTrue(is_valid)
        self.assertFalse(res['blocked'])
        self.assertEqual(res['status'], 'OK')
        self.assertEqual(len(res['missing_fields']), 0)

    def test_validate_missing_food_cost_blocks(self):
        """GA-007 시나리오: Food_Cost 결측 시 DATA_INCOMPLETE 및 차단 검증"""
        missing_fc_rec = {
            'Date': '46255',
            'Sales': 11200000,
            'Guests': 340,
            'Labor_Cost': 2950000,
            'Food_Cost': '', # MISSING
            'Incoming_kg': 160.0,
            'Sold_kg': 150.0,
            'Waste_kg': 1.0,
            'Actual_End_kg': 10.0
        }
        is_valid, res = validate_required_fields(missing_fc_rec)
        self.assertFalse(is_valid)
        self.assertTrue(res['blocked'])
        self.assertEqual(res['status'], 'DATA_INCOMPLETE')
        self.assertIn('Food_Cost', res['missing_fields'])

    def test_no_data_mutation(self):
        """GP-02: 원본 레코드를 임의 변경(0으로 채우기 등)하지 않음을 검증"""
        orig_rec = {'Date': '46255', 'Food_Cost': ''}
        validate_required_fields(orig_rec)
        self.assertEqual(orig_rec['Food_Cost'], '')

if __name__ == '__main__':
    unittest.main()

