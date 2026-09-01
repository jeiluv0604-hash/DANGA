# -*- coding: utf-8 -*-
from typing import Optional, Union

def calculate_food_cost(raw_cost: Union[int, float, str]) -> float:
    if raw_cost is None or raw_cost == '':
        raise ValueError('Food_Cost cannot be empty')
    val = float(raw_cost)
    if val < 0:
        raise ValueError('Food_Cost cannot be negative')
    return val

def calculate_food_cost_ratio(food_cost: float, sales: float) -> Optional[float]:
    """
    식재료 원가율 = Food_Cost / Sales
    Sales가 0 이하이면 None 반환
    """
    if food_cost is None or sales is None:
        return None
    if sales <= 0:
        return None
    return food_cost / sales

