# -*- coding: utf-8 -*-
from typing import Optional

def calculate_contribution(sales: float, food_cost: float, labor_cost: float) -> Optional[float]:
    """
    공헌이익 = Sales - Food_Cost - Labor_Cost
    """
    if sales is None or food_cost is None or labor_cost is None:
        return None
    return round(float(sales) - float(food_cost) - float(labor_cost), 2)

def calculate_contribution_ratio(contribution: float, sales: float) -> Optional[float]:
    """
    공헌이익률 = Contribution / Sales
    """
    if contribution is None or sales is None:
        return None
    if sales <= 0:
        return None
    return contribution / sales

