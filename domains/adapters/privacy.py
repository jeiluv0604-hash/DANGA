# -*- coding: utf-8 -*-
from typing import List, Dict, Any
import re

SENSITIVE_PATTERNS = [
    r'주민.*번호',
    r'rrn',
    r'ssn',
    r'휴대폰',
    r'전화.*번호',
    r'phone',
    r'mobile',
    r'주소',
    r'address',
    r'카드.*번호',
    r'card.*num',
    r'계좌.*번호',
    r'account.*num',
    r'email',
    r'이메일',
    r'고객.*명',
    r'customer.*name',
    r'생년월일'
]

class SensitiveColumnDetector:
    """
    Scans column headers for PII / Sensitive personal data.
    If detected, blocks or flags import as REVIEW_REQUIRED.
    """
    @staticmethod
    def scan_columns(columns: List[str]) -> List[str]:
        detected = []
        for col in columns:
            normalized = col.strip().lower().replace(' ', '').replace('_', '')
            for pat in SENSITIVE_PATTERNS:
                if re.search(pat, normalized, re.IGNORECASE):
                    detected.append(col)
                    break
        return list(set(detected))

    @staticmethod
    def mask_sample_value(field_name: str, val: Any) -> Any:
        if val is None:
            return None
        s = str(val)
        if len(s) <= 2:
            return '*' * len(s)
        return s[0] + ('*' * (len(s) - 2)) + s[-1]

