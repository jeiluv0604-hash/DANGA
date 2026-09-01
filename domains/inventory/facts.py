# -*- coding: utf-8 -*-
from typing import Optional, Union

def calculate_theory_end(previous_end_kg: float,
                         incoming_kg: float,
                         sold_kg: float,
                         service_kg: float = 0.0,
                         waste_kg: float = 0.0) -> float:
    """
    이론재고 = 전일재고 + 입고량 - (판매량 + 서비스량 + 폐기량)
    """
    prev = float(previous_end_kg or 0.0)
    inc = float(incoming_kg or 0.0)
    sold = float(sold_kg or 0.0)
    svc = float(service_kg or 0.0)
    wst = float(waste_kg or 0.0)
    return round(prev + inc - (sold + svc + wst), 3)

def calculate_inventory_variance(actual_end_kg: float, theory_end_kg: float) -> float:
    """
    재고차이 = 실사재고 - 이론재고
    음수이면 실재고 부족
    """
    if actual_end_kg is None or theory_end_kg is None:
        raise ValueError('actual_end_kg and theory_end_kg are required')
    return round(float(actual_end_kg) - float(theory_end_kg), 3)

def calculate_waste_ratio(waste_kg: float, sold_kg: float) -> Optional[float]:
    """
    폐기율 = Waste_kg / Sold_kg
    Sold_kg가 0 이하이면 None 반환
    """
    if waste_kg is None or sold_kg is None:
        return None
    if sold_kg <= 0:
        return None
    return float(waste_kg) / float(sold_kg)

