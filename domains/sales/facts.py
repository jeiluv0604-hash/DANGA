# -*- coding: utf-8 -*-
from typing import Optional, Union

def calculate_sales(raw_sales: Union[int, float, str]) -> float:
    if raw_sales is None or raw_sales == '':
        raise ValueError('Sales cannot be empty')
    val = float(raw_sales)
    if val < 0:
        raise ValueError('Sales cannot be negative')
    return val

def calculate_guests(raw_guests: Union[int, float, str]) -> int:
    if raw_guests is None or raw_guests == '':
        raise ValueError('Guests cannot be empty')
    val = int(raw_guests)
    if val < 0:
        raise ValueError('Guests cannot be negative')
    return val

def calculate_avg_check(sales: float, guests: int) -> Optional[float]:
    """
    객단가 = Sales / Guests
    Guests가 0 이하이거나 유효하지 않으면 None 반환
    """
    if sales is None or guests is None:
        return None
    if guests <= 0:
        return None
    return round(sales / guests, 2)

