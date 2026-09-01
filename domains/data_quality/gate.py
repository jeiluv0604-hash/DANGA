# -*- coding: utf-8 -*-
import math
from typing import Dict, Any, List, Tuple

SCHEMA_CONTRACT = {
    'Date': {'type': 'any', 'required': True, 'nullable': False},
    'Sales': {'type': 'float', 'required': True, 'nullable': False, 'min': 0},
    'Guests': {'type': 'int', 'required': True, 'nullable': False, 'min': 1},
    'Labor_Cost': {'type': 'float', 'required': True, 'nullable': False, 'min': 0},
    'Food_Cost': {'type': 'float', 'required': True, 'nullable': False, 'min': 0},
    'Incoming_kg': {'type': 'float', 'required': True, 'nullable': False, 'min': 0},
    'Sold_kg': {'type': 'float', 'required': True, 'nullable': False, 'min': 0},
    'Service_kg': {'type': 'float', 'required': False, 'nullable': True, 'min': 0},
    'Waste_kg': {'type': 'float', 'required': True, 'nullable': False, 'min': 0},
    'Actual_End_kg': {'type': 'float', 'required': True, 'nullable': False, 'min': 0},
    'Theory_End_kg': {'type': 'float', 'required': False, 'nullable': True, 'min': 0},
    'Rating': {'type': 'float', 'required': False, 'nullable': True, 'min': 0.0, 'max': 5.0},
    'Review_Count': {'type': 'int', 'required': False, 'nullable': True, 'min': 0},
    'Complaints': {'type': 'int', 'required': False, 'nullable': True, 'min': 0}
}

def is_empty_or_invalid(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, str):
        val_s = val.strip()
        if val_s == '' or val_s.upper() in ('NULL', 'NONE', 'NAN', 'N/A'):
            return True
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return True
    return False

def validate_field_value(field_name: str, val: Any, rule: Dict[str, Any]) -> Tuple[bool, str]:
    if is_empty_or_invalid(val):
        if rule.get('required', False) or not rule.get('nullable', True):
            return False, f'{field_name} is required but missing/null'
        return True, ''

    target_type = rule.get('type')
    try:
        if target_type == 'int':
            if isinstance(val, str) and not val.strip().lstrip('-').isdigit():
                return False, f'{field_name} must be integer, got \"{val}\"'
            num_val = int(val)
        elif target_type == 'float':
            num_val = float(val)
            if math.isnan(num_val) or math.isinf(num_val):
                return False, f'{field_name} is NaN or Inf'
        else:
            return True, ''
    except (ValueError, TypeError):
        return False, f'{field_name} invalid numeric format: {val}'

    if 'min' in rule and num_val < rule['min']:
        min_val = rule['min']
        return False, f"{field_name} value {num_val} < min ({min_val})"
    if 'max' in rule and num_val > rule['max']:
        max_val = rule['max']
        return False, f"{field_name} value {num_val} > max ({max_val})"

    return True, ''

def validate_required_fields(record: Dict[str, Any], required_fields: List[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    GP-02 및 GP-10 강제: 필수 데이터 스키마 검증 게이트
    누락, 결측, NaN, 음수, 잘못된 타입 발견 시 즉시 차단(blocked=True, status='DATA_INCOMPLETE').
    임의 보정/대체(0, 평균값, 이전일자) 금지.
    """
    invalid_fields = []
    reasons = []

    fields_to_check = required_fields if required_fields else list(SCHEMA_CONTRACT.keys())
    for f in fields_to_check:
        rule = SCHEMA_CONTRACT.get(f, {'required': True, 'nullable': False})
        val = record.get(f)
        ok, reason = validate_field_value(f, val, rule)
        if not ok:
            invalid_fields.append(f)
            reasons.append(reason)

    if invalid_fields:
        return False, {
            'status': 'DATA_INCOMPLETE',
            'blocked': True,
            'missing_fields': invalid_fields,
            'reason': '; '.join(reasons)
        }

    return True, {
        'status': 'OK',
        'blocked': False,
        'missing_fields': [],
        'reason': None
    }


