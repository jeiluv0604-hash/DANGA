# -*- coding: utf-8 -*-
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.database import Base, get_db
from apps.api.main import app
from domains.management.prototype import (
    POLICY_STATUS,
    build_management_prototype,
    calculate_cash_flow,
    calculate_menu_cost,
    calculate_monthly_pnl,
    classify_menu_abcd,
    validate_action_transition,
)


def test_prototype_identity_and_disclosure():
    payload = build_management_prototype()
    assert payload["brand_name"] == "담가화로구이"
    assert payload["dataset_type"] == "SYNTHETIC"
    assert "실제 담가화로구이 매장 데이터 아님" in payload["data_disclosure"]


def test_all_three_user_policies_are_unverified():
    payload = build_management_prototype()
    assert payload["finance"]["allocation_policy_status"] == POLICY_STATUS
    assert payload["menu_engineering"]["policy"]["status"] == POLICY_STATUS
    assert payload["organization"]["scorecard_policy_status"] == POLICY_STATUS


def test_all_ten_daily_management_kpis_have_synthetic_values():
    snapshot = build_management_prototype()["daily_kpi_snapshot"]
    assert len(snapshot) == 10
    assert [item["order"] for item in snapshot] == list(range(1, 11))
    assert all(item["status"] == "AVAILABLE" for item in snapshot)


def test_six_month_sales_annualizes_to_verified_baseline():
    payload = build_management_prototype()
    six_month_sales = sum(row["sales"] for row in payload["finance"]["monthly_pnl"])
    assert len(payload["finance"]["monthly_pnl"]) == 6
    assert six_month_sales == 2_100_000_000
    assert payload["finance"]["annualized_sales_baseline"] == 4_200_000_000


def test_monthly_pnl_equation_is_deterministic():
    for row in build_management_prototype()["finance"]["monthly_pnl"]:
        expected = row["sales"] - sum(
            row[key]
            for key in ("food_cost", "labor_cost", "rent", "utilities", "card_platform_fees", "other_expenses")
        )
        assert row["operating_profit"] == expected
        assert row["data_status"] == "OK"


def test_monthly_pnl_missing_input_blocks_only_derived_values():
    row = calculate_monthly_pnl(
        {
            "period": "2026-09",
            "sales": 100,
            "food_cost": None,
            "labor_cost": 20,
            "rent": 10,
            "utilities": 5,
            "card_platform_fees": 3,
            "other_expenses": 2,
        }
    )
    assert row["sales"] == 100
    assert row["data_status"] == "DATA_INCOMPLETE"
    assert row["operating_profit"] is None
    assert row["missing_fields"] == ["food_cost"]


def test_budget_actual_variance_reconciles():
    for row in build_management_prototype()["finance"]["budget_actual"]:
        for metric in row["metrics"].values():
            assert metric["variance"] == metric["actual"] - metric["budget"]


def test_cash_flow_rolls_forward_without_gap():
    flows = build_management_prototype()["finance"]["cash_flow"]
    for index, row in enumerate(flows):
        assert row["ending_cash"] == row["beginning_cash"] + row["cash_inflows"] - row["cash_outflows"]
        if index:
            assert row["beginning_cash"] == flows[index - 1]["ending_cash"]


def test_cash_flow_zero_is_not_missing():
    assert calculate_cash_flow(100, 0, 0)["ending_cash"] == 100


def test_recipe_bom_cost_equals_item_cost_sum():
    for menu in build_management_prototype()["menu_engineering"]["menus"]:
        assert menu["standard_cost"] == sum(item["cost"] for item in menu["recipe_items"])
        assert menu["unit_contribution"] == menu["net_price"] - menu["standard_cost"]


def test_recipe_missing_price_blocks_menu_cost():
    menu = calculate_menu_cost(
        {
            "menu_id": "M-X",
            "menu_name": "검증 메뉴",
            "net_price": 10000,
            "sales_quantity": 1,
            "recipe_items": [
                {"ingredient_id": "I-X", "ingredient_name": "미입력 재료", "quantity": 1, "unit_price": None, "yield_rate": 1}
            ],
        }
    )
    assert menu["data_status"] == "DATA_INCOMPLETE"
    assert menu["standard_cost"] is None


def test_abcd_classifier_all_quadrants():
    assert classify_menu_abcd(10, 10, 5, 5) == "A"
    assert classify_menu_abcd(10, 1, 5, 5) == "B"
    assert classify_menu_abcd(1, 10, 5, 5) == "C"
    assert classify_menu_abcd(1, 1, 5, 5) == "D"


def test_manager_scorecard_is_advisory_and_totals_100():
    organization = build_management_prototype()["organization"]
    assert organization["scorecard_total_weight"] == 100
    assert organization["automated_employment_decisions"] is False
    assert all(policy["status"] == POLICY_STATUS for policy in organization["approval_policies"])
    assert all(policy["automatic_execution"] is False for policy in organization["approval_policies"])
    assert all(policy["self_approval_allowed"] is False for policy in organization["approval_policies"])


def test_sops_are_linked_to_rules_and_actions():
    standards = build_management_prototype()["standards"]
    sop_ids = {sop["sop_id"] for sop in standards["sops"]}
    assert all(sop["linked_rule_ids"] for sop in standards["sops"])
    assert all(action["sop_id"] in sop_ids for action in standards["actions"])


def test_action_state_machine_accepts_and_rejects_expected_transitions():
    assert validate_action_transition("OPEN", "IN_PROGRESS") is True
    assert validate_action_transition("IN_PROGRESS", "CLOSED") is True
    assert validate_action_transition("CLOSED", "VERIFIED") is True
    assert validate_action_transition("OPEN", "VERIFIED") is False
    assert validate_action_transition("VERIFIED", "IN_PROGRESS") is False


def test_monthly_review_requires_human_approval():
    review = build_management_prototype()["monthly_review"]
    assert review["status"] == "REVIEW_REQUIRED"
    assert review["human_approval_required"] is True
    assert review["ai_calculated_numbers"] is False


def test_management_api_and_persistent_action_audit_chain():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        response = client.get("/api/v1/management/prototype")
        assert response.status_code == 200
        assert response.json()["brand_name"] == "담가화로구이"

        transition = client.post(
            "/api/v1/management/actions/ACT-SYN-002/transition",
            json={"new_status": "IN_PROGRESS", "actor_role": "GENERAL_MANAGER", "comment": "가상 검증 시작"},
        )
        assert transition.status_code == 200
        assert transition.json()["action"]["status"] == "IN_PROGRESS"

        invalid = client.post(
            "/api/v1/management/actions/ACT-SYN-002/transition",
            json={"new_status": "VERIFIED", "actor_role": "GENERAL_MANAGER"},
        )
        assert invalid.status_code == 409

        audit = client.get("/api/v1/management/actions/ACT-SYN-002/audit")
        assert audit.status_code == 200
        assert len(audit.json()) == 1
        assert audit.json()[0]["previous_hash"] == "GENESIS"
        assert len(audit.json()[0]["event_hash"]) == 64
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
