# -*- coding: utf-8 -*-
from typing import Dict, Any, List, Optional

def evaluate_data_quality_rule(dq_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    R-DQ-01: 데이터 품질 게이트 규칙 (최우선 실행)
    필수 KPI 결측 또는 타입/범위 오류 시 CRITICAL 경보 및 DATA_INCOMPLETE 반환
    """
    if dq_result.get('blocked'):
        return {
            'rule_id': 'R-DQ-01',
            'domain': 'DataQuality',
            'status': 'DATA_INCOMPLETE',
            'severity': 'CRITICAL',
            'actual': dq_result.get('missing_fields'),
            'threshold': 'Valid Schema Contract',
            'comparison': dq_result.get('reason', 'Schema validation failed'),
            'evidence_fields': dq_result.get('missing_fields', []),
            'blocked': True
        }
    return None

def evaluate_labor_rule(labor_ratio: Optional[float]) -> Optional[Dict[str, Any]]:
    """
    R-LAB-01: 인건비율 이상 규칙
    조건: Labor_Ratio >= 33% (0.33)
    """
    if labor_ratio is None:
        return None
    if labor_ratio >= 0.33:
        return {
            'rule_id': 'R-LAB-01',
            'domain': 'Labor',
            'status': 'ALERT',
            'severity': 'HIGH',
            'actual': round(labor_ratio, 4),
            'threshold': 0.33,
            'comparison': 'Labor_Ratio >= 33%',
            'evidence_fields': ['Labor_Cost', 'Sales', 'Labor_Ratio']
        }
    return None

def evaluate_inventory_variance_rule(variance_kg: Optional[float]) -> Optional[Dict[str, Any]]:
    """
    R-INV-01: 재고 불일치 이상 규칙
    조건: Variance_kg <= -5.0kg
    주의: 절도/부정행위로 단정하지 않고 확인 필요 이상으로만 판정 (GP-05)
    """
    if variance_kg is None:
        return None
    if variance_kg <= -5.0:
        return {
            'rule_id': 'R-INV-01',
            'domain': 'Inventory',
            'status': 'ALERT',
            'severity': 'CRITICAL',
            'actual': round(variance_kg, 3),
            'threshold': -5.0,
            'comparison': 'Variance_kg <= -5.0kg',
            'evidence_fields': ['Actual_End_kg', 'Theory_End_kg', 'Variance_kg']
        }
    return None

def evaluate_food_cost_rule(food_cost_ratio: Optional[float]) -> Optional[Dict[str, Any]]:
    """
    R-FC-01: 식재료 원가율 일일 이상 규칙
    조건: Food_Cost_Ratio >= 39% (0.39)
    """
    if food_cost_ratio is None:
        return None
    if food_cost_ratio >= 0.39:
        return {
            'rule_id': 'R-FC-01',
            'domain': 'FoodCost',
            'status': 'ALERT',
            'severity': 'HIGH',
            'actual': round(food_cost_ratio, 4),
            'threshold': 0.39,
            'comparison': 'Food_Cost_Ratio >= 39%',
            'evidence_fields': ['Food_Cost', 'Sales', 'Food_Cost_Ratio']
        }
    return None

def evaluate_waste_rule(waste_ratio: Optional[float]) -> Optional[Dict[str, Any]]:
    """
    R-WST-01: 폐기율 이상 규칙
    조건: Waste_Ratio >= 5% (0.05)
    """
    if waste_ratio is None:
        return None
    if waste_ratio >= 0.05:
        return {
            'rule_id': 'R-WST-01',
            'domain': 'Waste',
            'status': 'ALERT',
            'severity': 'HIGH',
            'actual': round(waste_ratio, 4),
            'threshold': 0.05,
            'comparison': 'Waste_Ratio >= 5%',
            'evidence_fields': ['Waste_kg', 'Sold_kg', 'Waste_Ratio']
        }
    return None

def evaluate_customer_rule(complaints: Optional[int], rating: Optional[float]) -> Optional[Dict[str, Any]]:
    """
    R-CUS-01: 고객 VOC 및 평점 이상 규칙
    조건: Complaints >= 5 OR Rating < 4.2
    """
    is_complaint_alert = complaints is not None and complaints >= 5
    is_rating_alert = rating is not None and rating < 4.2
    
    if is_complaint_alert or is_rating_alert:
        return {
            'rule_id': 'R-CUS-01',
            'domain': 'Customer',
            'status': 'ALERT',
            'severity': 'MEDIUM',
            'actual': {
                'complaints': complaints,
                'rating': rating
            },
            'threshold': 'Complaints >= 5 OR Rating < 4.2',
            'comparison': f'Complaints={complaints} (>=5: {is_complaint_alert}), Rating={rating} (<4.2: {is_rating_alert})',
            'evidence_fields': ['Complaints', 'Rating']
        }
    return None

def detect_food_cost_streak(daily_records: List[Dict[str, Any]],
                            threshold: float = 0.39,
                            min_consecutive_days: int = 7) -> List[Dict[str, Any]]:
    """
    일반화된 연속 식재료 원가율 급등 탐지 함수 (특정 날짜 하드코딩 없음)
    """
    detected_streaks = []
    current_streak = []
    
    for rec in daily_records:
        facts = rec.get('facts')
        fc_ratio = facts.get('food_cost_ratio') if facts else None
        
        if fc_ratio is not None and fc_ratio >= threshold:
            current_streak.append(rec)
        else:
            if len(current_streak) >= min_consecutive_days:
                ratios = [r['facts']['food_cost_ratio'] for r in current_streak]
                detected_streaks.append({
                    'rule_id': 'R-FC-01-PERIOD',
                    'domain': 'FoodCost',
                    'status': 'ALERT',
                    'severity': 'HIGH',
                    'start_date': current_streak[0]['date'],
                    'end_date': current_streak[-1]['date'],
                    'consecutive_days': len(current_streak),
                    'threshold': threshold,
                    'actual': {
                        'consecutive_days': len(current_streak),
                        'avg_ratio': round(sum(ratios) / len(ratios), 4)
                    },
                    'comparison': f'Food_Cost_Ratio >= {threshold:.0%} for {len(current_streak)} consecutive days ({current_streak[0]["date"]} ~ {current_streak[-1]["date"]})',
                    'evidence_fields': ['Food_Cost', 'Sales', 'Food_Cost_Ratio']
                })
            current_streak = []
            
    if len(current_streak) >= min_consecutive_days:
        ratios = [r['facts']['food_cost_ratio'] for r in current_streak]
        detected_streaks.append({
            'rule_id': 'R-FC-01-PERIOD',
            'domain': 'FoodCost',
            'status': 'ALERT',
            'severity': 'HIGH',
            'start_date': current_streak[0]['date'],
            'end_date': current_streak[-1]['date'],
            'consecutive_days': len(current_streak),
            'threshold': threshold,
            'actual': {
                'consecutive_days': len(current_streak),
                'avg_ratio': round(sum(ratios) / len(ratios), 4)
            },
            'comparison': f'Food_Cost_Ratio >= {threshold:.0%} for {len(current_streak)} consecutive days ({current_streak[0]["date"]} ~ {current_streak[-1]["date"]})',
            'evidence_fields': ['Food_Cost', 'Sales', 'Food_Cost_Ratio']
        })
        
    return detected_streaks

def detect_profit_reversal(records: List[Dict[str, Any]],
                           window_days: int = 7,
                           comparison: str = "previous_window") -> List[Dict[str, Any]]:
    """
    일반화된 Rolling Window 기반 매출-이익 역행 탐지 함수 (특정 날짜 하드코딩 없음)
    Target Window Sales > Baseline Window Sales AND Target Contrib Ratio < Baseline Contrib Ratio
    """
    valid_records = [r for r in records if r.get('facts') and r['facts'].get('sales') is not None and r['facts'].get('contribution') is not None]
    if len(valid_records) < window_days * 2:
        return []
        
    alerts = []
    for i in range(window_days, len(valid_records) - window_days + 1):
        baseline = valid_records[i - window_days : i]
        target = valid_records[i : i + window_days]
        
        b_sales = sum(r['facts']['sales'] for r in baseline)
        b_contrib = sum(r['facts']['contribution'] for r in baseline)
        t_sales = sum(r['facts']['sales'] for r in target)
        t_contrib = sum(r['facts']['contribution'] for r in target)
        
        if b_sales <= 0 or t_sales <= 0:
            continue
            
        b_ratio = b_contrib / b_sales
        t_ratio = t_contrib / t_sales
        
        if t_sales > b_sales and t_ratio < b_ratio:
            alerts.append({
                'rule_id': 'R-PRO-01',
                'domain': 'Profit',
                'status': 'ALERT',
                'severity': 'HIGH',
                'baseline_start': baseline[0]['date'],
                'baseline_end': baseline[-1]['date'],
                'target_start': target[0]['date'],
                'target_end': target[-1]['date'],
                'actual': {
                    'baseline_sales': b_sales,
                    'target_sales': t_sales,
                    'baseline_contribution_ratio': round(b_ratio, 4),
                    'target_contribution_ratio': round(t_ratio, 4)
                },
                'threshold': 'target_sales > baseline_sales AND target_contribution_ratio < baseline_contribution_ratio',
                'comparison': f'Sales increased ({b_sales:,.0f} -> {t_sales:,.0f}) but Contrib Ratio fell ({b_ratio:.1%} -> {t_ratio:.1%})',
                'evidence_fields': ['Sales', 'Contribution', 'Contribution_Ratio']
            })
            
    return alerts


RULES = [
    {
        "rule_id": "R-DQ-01",
        "rule_type": "DATA_QUALITY",
        "severity": "CRITICAL",
        "metric": "data_status",
        "threshold": "VALID",
        "operator": "==",
        "description": "데이터 품질 게이트 - 필수 KPI 결측 시 계산 차단"
    },
    {
        "rule_id": "R-LAB-01",
        "rule_type": "LABOR",
        "severity": "HIGH",
        "metric": "labor_ratio",
        "threshold": 0.33,
        "operator": ">=",
        "description": "인건비율 관리 기준(33.0%) 초과"
    },
    {
        "rule_id": "R-INV-01",
        "rule_type": "INVENTORY",
        "severity": "CRITICAL",
        "metric": "variance_kg",
        "threshold": -5.0,
        "operator": "<=",
        "description": "이론 재고 대비 실사 재고 차이(-5.0kg 이하) 발생"
    },
    {
        "rule_id": "R-FC-01",
        "rule_type": "FOOD_COST",
        "severity": "HIGH",
        "metric": "food_cost_ratio",
        "threshold": 0.39,
        "operator": ">=",
        "description": "일일 식재료 원가율 관리 기준(39.0%) 초과"
    },
    {
        "rule_id": "R-FC-01-PERIOD",
        "rule_type": "FOOD_COST_PERIOD",
        "severity": "HIGH",
        "metric": "food_cost_ratio",
        "threshold": 0.39,
        "operator": ">= 7d",
        "description": "주간 연속 7일 고원가율(39.0% 이상) 지속"
    },
    {
        "rule_id": "R-WST-01",
        "rule_type": "WASTE",
        "severity": "HIGH",
        "metric": "waste_ratio",
        "threshold": 0.05,
        "operator": ">=",
        "description": "식재료 폐기율 관리 기준(5.0%) 초과"
    },
    {
        "rule_id": "R-CUS-01",
        "rule_type": "CUSTOMER",
        "severity": "MEDIUM",
        "metric": "complaints_or_rating",
        "threshold": "complaints>=5 OR rating<4.2",
        "operator": "OR",
        "description": "고객 불만(5건 이상) 또는 평점(4.2 미만) 이상"
    },
    {
        "rule_id": "R-PRO-01",
        "rule_type": "PROFIT",
        "severity": "HIGH",
        "metric": "contribution_ratio",
        "threshold": "Reversal",
        "operator": "reversal",
        "description": "매출 증가에도 공헌이익률 하락(수익성 역행)"
    }
]



