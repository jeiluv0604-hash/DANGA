# -*- coding: utf-8 -*-
import datetime
from typing import Dict, Any, List, Optional

from domains.data_quality.gate import validate_required_fields
from domains.sales.facts import calculate_sales, calculate_guests, calculate_avg_check
from domains.labor.facts import calculate_labor_cost, calculate_labor_ratio
from domains.food_cost.facts import calculate_food_cost, calculate_food_cost_ratio
from domains.inventory.facts import calculate_theory_end, calculate_inventory_variance, calculate_waste_ratio
from domains.customer.facts import calculate_daily_rating, calculate_complaints, calculate_review_count
from domains.management.facts import calculate_contribution, calculate_contribution_ratio
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

def excel_serial_to_date_str(serial: Any) -> str:
    try:
        val = float(serial)
        base = datetime.datetime(1899, 12, 30)
        dt = base + datetime.timedelta(days=val)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return str(serial)

def process_daily_record(record: Dict[str, Any], prev_actual_end_kg: float = 0.0) -> Dict[str, Any]:
    """
    일일 데이터 파이프라인 (Data -> Quality Gate -> Partial Facts -> Rules -> Alerts)
    원칙: 독립적으로 유효한 Facts는 보존하고, 결측 필드에 종속된 KPI만 Null 처리.
    """
    raw_date = record.get('Date', '')
    date_str = excel_serial_to_date_str(raw_date)
    
    # 1. Data Quality Gate (GP-02, GP-10)
    is_valid, dq_result = validate_required_fields(record)
    missing_fields = dq_result.get('missing_fields', [])
    data_status = 'OK' if is_valid else 'DATA_INCOMPLETE'
    blocked = not is_valid
    ai_eligible = is_valid

    kpi_status = {}

    # 2. Field-Level Independent & Dependent Facts Calculation
    # A. Sales & Guests
    if 'Sales' not in missing_fields and record.get('Sales') not in (None, ''):
        try:
            sales = calculate_sales(record['Sales'])
            kpi_status['sales'] = 'AVAILABLE'
        except Exception:
            sales = None
            kpi_status['sales'] = 'INVALID_FORMAT'
    else:
        sales = None
        kpi_status['sales'] = 'MISSING_INPUT'

    if 'Guests' not in missing_fields and record.get('Guests') not in (None, ''):
        try:
            guests = calculate_guests(record['Guests'])
            kpi_status['guests'] = 'AVAILABLE'
        except Exception:
            guests = None
            kpi_status['guests'] = 'INVALID_FORMAT'
    else:
        guests = None
        kpi_status['guests'] = 'MISSING_INPUT'

    if sales is not None and guests is not None:
        avg_check = calculate_avg_check(sales, guests)
        kpi_status['avg_check'] = 'AVAILABLE'
    else:
        avg_check = None
        kpi_status['avg_check'] = 'BLOCKED_DEPENDENCY'

    # B. Labor
    if 'Labor_Cost' not in missing_fields and record.get('Labor_Cost') not in (None, ''):
        try:
            labor_cost = calculate_labor_cost(record['Labor_Cost'])
            kpi_status['labor_cost'] = 'AVAILABLE'
        except Exception:
            labor_cost = None
            kpi_status['labor_cost'] = 'INVALID_FORMAT'
    else:
        labor_cost = None
        kpi_status['labor_cost'] = 'MISSING_INPUT'

    if labor_cost is not None and sales is not None and sales > 0:
        labor_ratio = calculate_labor_ratio(labor_cost, sales)
        kpi_status['labor_ratio'] = 'AVAILABLE'
    else:
        labor_ratio = None
        kpi_status['labor_ratio'] = 'BLOCKED_DEPENDENCY'

    # C. Food Cost
    if 'Food_Cost' not in missing_fields and record.get('Food_Cost') not in (None, ''):
        try:
            food_cost = calculate_food_cost(record['Food_Cost'])
            kpi_status['food_cost'] = 'AVAILABLE'
        except Exception:
            food_cost = None
            kpi_status['food_cost'] = 'INVALID_FORMAT'
    else:
        food_cost = None
        kpi_status['food_cost'] = 'MISSING_INPUT'

    if food_cost is not None and sales is not None and sales > 0:
        food_cost_ratio = calculate_food_cost_ratio(food_cost, sales)
        kpi_status['food_cost_ratio'] = 'AVAILABLE'
    else:
        food_cost_ratio = None
        kpi_status['food_cost_ratio'] = 'BLOCKED_DEPENDENCY'

    # D. Inventory & Waste
    def safe_float(fld):
        v = record.get(fld)
        if v in (None, ''): return None
        try: return float(v)
        except: return None

    incoming_kg = safe_float('Incoming_kg')
    sold_kg = safe_float('Sold_kg')
    waste_kg = safe_float('Waste_kg')
    actual_end_kg = safe_float('Actual_End_kg')

    # Service_kg semantics (Phase 2.2):
    # 0 or 0.0 -> AVAILABLE (value: 0.0)
    # None or '' -> NOT_PROVIDED (value: None)
    raw_service = record.get('Service_kg')
    if raw_service is not None and str(raw_service).strip() != '':
        try:
            service_kg = float(raw_service)
            kpi_status['service_kg'] = 'AVAILABLE'
        except Exception:
            service_kg = None
            kpi_status['service_kg'] = 'INVALID_FORMAT'
    else:
        service_kg = None
        kpi_status['service_kg'] = 'NOT_PROVIDED'

    if waste_kg is not None and sold_kg is not None and sold_kg > 0:
        waste_ratio = calculate_waste_ratio(waste_kg, sold_kg)
        kpi_status['waste_ratio'] = 'AVAILABLE'
    else:
        waste_ratio = None
        kpi_status['waste_ratio'] = 'BLOCKED_DEPENDENCY' if ('Waste_kg' in missing_fields or 'Sold_kg' in missing_fields) else 'NOT_PROVIDED'

    # Theory_End_kg semantics:
    # 1. Directly provided in record
    raw_theory = record.get('Theory_End_kg')
    if raw_theory is not None and str(raw_theory).strip() != '':
        theory_end_kg = safe_float('Theory_End_kg')
        kpi_status['theory_end_kg'] = 'AVAILABLE'
    # 2. Calculated from stock movement: requires prev_actual_end_kg, incoming_kg, sold_kg, service_kg (MUST NOT be None), waste_kg
    elif incoming_kg is not None and sold_kg is not None and service_kg is not None and waste_kg is not None:
        theory_end_kg = calculate_theory_end(prev_actual_end_kg, incoming_kg, sold_kg, service_kg, waste_kg)
        kpi_status['theory_end_kg'] = 'AVAILABLE'
    else:
        theory_end_kg = None
        kpi_status['theory_end_kg'] = 'BLOCKED_DEPENDENCY'

    if actual_end_kg is not None and theory_end_kg is not None:
        variance_kg = calculate_inventory_variance(actual_end_kg, theory_end_kg)
        kpi_status['inventory_variance'] = 'AVAILABLE'
    else:
        variance_kg = None
        kpi_status['inventory_variance'] = 'BLOCKED_DEPENDENCY'

    # E. Customer
    rating = calculate_daily_rating(record.get('Rating'))
    complaints = calculate_complaints(record.get('Complaints'))
    review_count = calculate_review_count(record.get('Review_Count'))
    kpi_status['rating'] = 'AVAILABLE' if rating is not None else 'NOT_PROVIDED'
    kpi_status['complaints'] = 'AVAILABLE' if complaints is not None else 'NOT_PROVIDED'
    kpi_status['review_count'] = 'AVAILABLE' if review_count is not None else 'NOT_PROVIDED'


    # F. Contribution
    if sales is not None and food_cost is not None and labor_cost is not None:
        contribution = calculate_contribution(sales, food_cost, labor_cost)
        contribution_ratio = calculate_contribution_ratio(contribution, sales)
        kpi_status['contribution'] = 'AVAILABLE'
        kpi_status['contribution_ratio'] = 'AVAILABLE'
    else:
        contribution = None
        contribution_ratio = None
        kpi_status['contribution'] = 'BLOCKED_DEPENDENCY'
        kpi_status['contribution_ratio'] = 'BLOCKED_DEPENDENCY'

    facts = {
        'sales': sales,
        'guests': guests,
        'avg_check': avg_check,
        'labor_cost': labor_cost,
        'labor_ratio': labor_ratio,
        'food_cost': food_cost,
        'food_cost_ratio': food_cost_ratio,
        'incoming_kg': incoming_kg,
        'sold_kg': sold_kg,
        'service_kg': service_kg,
        'waste_kg': waste_kg,
        'theory_end_kg': theory_end_kg,
        'actual_end_kg': actual_end_kg,
        'variance_kg': variance_kg,
        'waste_ratio': waste_ratio,
        'rating': rating,
        'complaints': complaints,
        'review_count': review_count,
        'contribution': contribution,
        'contribution_ratio': contribution_ratio,
        'kpi_status': kpi_status
    }

    # 3. Rule Engine
    alerts = []
    triggered_rule_ids = []

    if not is_valid:
        dq_alert = evaluate_data_quality_rule(dq_result)
        if dq_alert:
            alerts.append(dq_alert)
            triggered_rule_ids.append(dq_alert['rule_id'])

    if labor_ratio is not None:
        lab_alert = evaluate_labor_rule(labor_ratio)
        if lab_alert:
            alerts.append(lab_alert)
            triggered_rule_ids.append(lab_alert['rule_id'])

    if variance_kg is not None:
        inv_alert = evaluate_inventory_variance_rule(variance_kg)
        if inv_alert:
            alerts.append(inv_alert)
            triggered_rule_ids.append(inv_alert['rule_id'])

    if food_cost_ratio is not None:
        fc_alert = evaluate_food_cost_rule(food_cost_ratio)
        if fc_alert:
            alerts.append(fc_alert)
            triggered_rule_ids.append(fc_alert['rule_id'])

    if waste_ratio is not None:
        wst_alert = evaluate_waste_rule(waste_ratio)
        if wst_alert:
            alerts.append(wst_alert)
            triggered_rule_ids.append(wst_alert['rule_id'])

    if rating is not None or complaints is not None:
        cus_alert = evaluate_customer_rule(complaints, rating)
        if cus_alert:
            alerts.append(cus_alert)
            triggered_rule_ids.append(cus_alert['rule_id'])

    return {
        'date': date_str,
        'raw_date': raw_date,
        'data_status': data_status,
        'blocked': blocked,
        'ai_eligible': ai_eligible,
        'missing_fields': missing_fields,
        'facts': facts,
        'alerts': alerts,
        'triggered_rule_ids': sorted(list(set(triggered_rule_ids)))
    }


def run_full_pipeline(daily_operations_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    전체 일일 데이터를 순차 처리하고 Facts 및 룰 판정 결과 반환
    """
    results = []
    prev_end = 0.0
    for row in daily_operations_rows:
        res = process_daily_record(row, prev_actual_end_kg=prev_end)
        if res.get('facts') and res['facts'].get('actual_end_kg') is not None:
            prev_end = res['facts']['actual_end_kg']
        results.append(res)
        
    return results






