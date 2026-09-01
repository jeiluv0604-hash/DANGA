# -*- coding: utf-8 -*-
from typing import Optional, Union

def calculate_daily_rating(raw_rating: Union[int, float, str, None]) -> Optional[float]:
    """
    일일 평점 계산: 결측 시 None 반환 (0으로 채우지 않음)
    """
    if raw_rating is None or raw_rating == '':
        return None
    val = float(raw_rating)
    if val < 0 or val > 5:
        raise ValueError('Rating must be between 0 and 5')
    return round(val, 2)

def calculate_complaints(raw_complaints: Union[int, float, str, None]) -> Optional[int]:
    """
    클레임 건수 계산: 결측 시 None 반환 (실제 0건과 결측을 엄격히 구분)
    """
    if raw_complaints is None or raw_complaints == '':
        return None
    val = int(raw_complaints)
    if val < 0:
        raise ValueError('Complaints cannot be negative')
    return val

def calculate_review_count(raw_count: Union[int, float, str, None]) -> Optional[int]:
    """
    리뷰 수 계산: 결측 시 None 반환 (실제 0건과 결측을 엄격히 구분)
    """
    if raw_count is None or raw_count == '':
        return None
    val = int(raw_count)
    if val < 0:
        raise ValueError('Review_Count cannot be negative')
    return val


