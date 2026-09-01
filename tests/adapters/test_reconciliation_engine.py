# -*- coding: utf-8 -*-
from domains.adapters.reconciliation import ReconciliationEngine

def test_rec_01_exact_match():
    rows = [
        {"net_sales": 100000, "cancelled": False},
        {"net_sales": 50000, "cancelled": False}
    ]
    rep = ReconciliationEngine.reconcile_pos_sales("IMP-01", rows, expected_daily_sales=150000)
    assert rep.overall_status == "MATCH"
    assert rep.metrics[0].diff_abs == 0.0

def test_rec_02_minor_mismatch():
    rows = [
        {"net_sales": 100000, "cancelled": False},
        {"net_sales": 51000, "cancelled": False}
    ]
    # 151,000 vs 150,000 -> 1,000 diff (0.66% diff <= 2%)
    rep = ReconciliationEngine.reconcile_pos_sales("IMP-01", rows, expected_daily_sales=150000)
    assert rep.overall_status == "MINOR_MISMATCH"

def test_rec_03_major_mismatch():
    rows = [
        {"net_sales": 100000, "cancelled": False}
    ]
    # 100,000 vs 150,000 -> 33% diff > 2%
    rep = ReconciliationEngine.reconcile_pos_sales("IMP-01", rows, expected_daily_sales=150000)
    assert rep.overall_status == "MAJOR_MISMATCH"

def test_rec_04_not_comparable():
    rows = [
        {"item_id": "ITM-01", "quantity": 10, "unit_price": 5000, "source_amount": None, "amount": None}
    ]
    rep = ReconciliationEngine.reconcile_purchases("IMP-01", rows)
    assert rep.overall_status == "NOT_COMPARABLE"

def test_rec_05_pos_daily_aggregation():
    rows = [
        {"net_sales": 70000, "cancelled": False},
        {"net_sales": 8000, "cancelled": False}
    ]
    rep = ReconciliationEngine.reconcile_pos_sales("IMP-01", rows)
    assert rep.overall_status == "MATCH"
    assert rep.metrics[0].source_value == 78000

def test_rec_06_purchase_calc_vs_invoice():
    rows = [
        {"item_id": "ITM-01", "quantity": 10, "unit_price": 5000, "source_amount": 50000, "amount": 50000}
    ]
    rep = ReconciliationEngine.reconcile_purchases("IMP-01", rows)
    assert rep.overall_status == "MATCH"
    assert rep.metrics[0].calculated_value == 50000

