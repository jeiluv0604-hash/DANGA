# -*- coding: utf-8 -*-
from domains.adapters.privacy import SensitiveColumnDetector
from domains.adapters.quarantine import QuarantineManager

def test_privacy_sensitive_columns_detection():
    cols = ["주민등록번호", "전화번호", "휴대폰", "고객주소", "카드번호", "영수증번호", "실매출"]
    detected = SensitiveColumnDetector.scan_columns(cols)
    assert "주민등록번호" in detected
    assert "전화번호" in detected
    assert "휴대폰" in detected
    assert "고객주소" in detected
    assert "카드번호" in detected
    assert "실매출" not in detected
    assert "영수증번호" not in detected

def test_privacy_masked_sample_value():
    assert SensitiveColumnDetector.mask_sample_value("phone", "010-1234-5678") == "0***********8"
    assert SensitiveColumnDetector.mask_sample_value("name", "홍길동") == "홍*동"
    assert SensitiveColumnDetector.mask_sample_value("short", "ab") == "**"
    assert SensitiveColumnDetector.mask_sample_value("none", None) is None

def test_quarantine_record_generation():
    q = QuarantineManager.create_record("source.csv", 10, "INVALID_NUMBER", field_name="quantity", raw_val="abc")
    assert q.quarantine_id.startswith("QRN-")
    assert q.source_file == "source.csv"
    assert q.source_row == 10
    assert q.reason == "INVALID_NUMBER"
    assert q.field_name == "quantity"
    assert q.safe_value_preview == "abc"

