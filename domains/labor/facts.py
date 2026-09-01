# -*- coding: utf-8 -*-
from typing import Optional, Union

def calculate_labor_cost(raw_cost: Union[int, float, str]) -> float:
    if raw_cost is None or raw_cost == '':
        raise ValueError('Labor_Cost cannot be empty')
    val = float(raw_cost)
    if val < 0:
        raise ValueError('Labor_Cost cannot be negative')
    return val

def calculate_labor_ratio(labor_cost: float, sales: float) -> Optional[float]:
    """
    인건비율 = Labor_Cost / Sales
    Sales가 0 이하이면 None 반환
    """
    if labor_cost is None or sales is None:
        return None
    if sales <= 0:
        return None
    return labor_cost / sales

