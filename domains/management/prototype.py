# -*- coding: utf-8 -*-
"""Deterministic management-system prototype for 담가화로구이.

All values in this module are synthetic.  The module deliberately keeps
policy-dependent thresholds separate from facts and labels them
``UNVERIFIED POLICY`` so a prototype value can never be mistaken for an
approved operating policy.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from statistics import median
from typing import Any, Dict, Iterable, List


BRAND_NAME = "담가화로구이"
DATASET_TYPE = "SYNTHETIC"
POLICY_STATUS = "UNVERIFIED POLICY"
PROTOTYPE_VERSION = "6.0.0-prototype"


def _money(value: Decimal | int | str) -> int:
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def calculate_monthly_pnl(row: Dict[str, int]) -> Dict[str, Any]:
    """Calculate a monthly P&L without estimates or LLM involvement."""
    required = (
        "sales",
        "food_cost",
        "labor_cost",
        "rent",
        "utilities",
        "card_platform_fees",
        "other_expenses",
    )
    missing = [key for key in required if row.get(key) is None]
    if missing:
        return {
            **row,
            "data_status": "DATA_INCOMPLETE",
            "missing_fields": missing,
            "operating_profit": None,
            "operating_margin": None,
        }
    operating_expenses = sum(int(row[key]) for key in required if key != "sales")
    operating_profit = int(row["sales"]) - operating_expenses
    return {
        **row,
        "operating_expenses": operating_expenses,
        "operating_profit": operating_profit,
        "operating_margin": _ratio(operating_profit, int(row["sales"])),
        "food_cost_ratio": _ratio(int(row["food_cost"]), int(row["sales"])),
        "labor_ratio": _ratio(int(row["labor_cost"]), int(row["sales"])),
        "data_status": "OK",
        "missing_fields": [],
    }


def calculate_budget_actual(actual: Dict[str, int], budget: Dict[str, int]) -> Dict[str, Any]:
    metrics = ("sales", "food_cost", "labor_cost", "operating_profit")
    result: Dict[str, Any] = {"period": actual["period"], "metrics": {}}
    for metric in metrics:
        actual_value = int(actual[metric])
        budget_value = int(budget[metric])
        variance = actual_value - budget_value
        result["metrics"][metric] = {
            "actual": actual_value,
            "budget": budget_value,
            "variance": variance,
            "variance_ratio": _ratio(variance, budget_value),
        }
    return result


def calculate_cash_flow(beginning_cash: int, inflows: int, outflows: int) -> Dict[str, int]:
    return {
        "beginning_cash": int(beginning_cash),
        "cash_inflows": int(inflows),
        "cash_outflows": int(outflows),
        "ending_cash": int(beginning_cash) + int(inflows) - int(outflows),
    }


def calculate_menu_cost(menu: Dict[str, Any]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    total_cost = 0
    missing: List[str] = []
    for item in menu["recipe_items"]:
        if item.get("quantity") is None or item.get("unit_price") is None or item.get("yield_rate") in (None, 0):
            missing.append(item["ingredient_id"])
            continue
        effective_quantity = Decimal(str(item["quantity"])) / Decimal(str(item["yield_rate"]))
        cost = _money(effective_quantity * Decimal(str(item["unit_price"])))
        total_cost += cost
        items.append({**item, "effective_quantity": float(effective_quantity), "cost": cost})
    if missing:
        return {
            **menu,
            "recipe_items": items,
            "standard_cost": None,
            "unit_contribution": None,
            "contribution_margin": None,
            "data_status": "DATA_INCOMPLETE",
            "missing_ingredients": missing,
        }
    unit_contribution = int(menu["net_price"]) - total_cost
    return {
        **menu,
        "recipe_items": items,
        "standard_cost": total_cost,
        "unit_contribution": unit_contribution,
        "contribution_margin": _ratio(unit_contribution, int(menu["net_price"])),
        "data_status": "OK",
        "missing_ingredients": [],
    }


def classify_menu_abcd(
    sales_quantity: int,
    unit_contribution: int,
    quantity_threshold: float,
    contribution_threshold: float,
) -> str:
    high_sales = sales_quantity >= quantity_threshold
    high_contribution = unit_contribution >= contribution_threshold
    if high_sales and high_contribution:
        return "A"
    if high_sales and not high_contribution:
        return "B"
    if not high_sales and high_contribution:
        return "C"
    return "D"


def validate_action_transition(current_status: str, new_status: str) -> bool:
    allowed = {
        "OPEN": {"IN_PROGRESS", "CANCELLED"},
        "IN_PROGRESS": {"CLOSED", "BLOCKED", "CANCELLED"},
        "BLOCKED": {"IN_PROGRESS", "CANCELLED"},
        "CLOSED": {"VERIFIED", "REOPENED"},
        "REOPENED": {"IN_PROGRESS", "CANCELLED"},
        "VERIFIED": set(),
        "CANCELLED": set(),
    }
    return new_status in allowed.get(current_status, set())


def _synthetic_finance() -> Dict[str, Any]:
    periods = ["2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"]
    sales_values = [342_000_000, 348_000_000, 355_000_000, 351_000_000, 360_000_000, 344_000_000]
    food_rates = ["0.340", "0.345", "0.350", "0.338", "0.342", "0.336"]
    labor_rates = ["0.285", "0.281", "0.290", "0.278", "0.283", "0.280"]
    utility_values = [19_000_000, 18_000_000, 20_000_000, 22_000_000, 23_000_000, 21_000_000]
    monthly: List[Dict[str, Any]] = []
    budgets: List[Dict[str, int]] = []
    cash_flows: List[Dict[str, Any]] = []
    beginning_cash = 180_000_000

    for index, period in enumerate(periods):
        sales = sales_values[index]
        row = calculate_monthly_pnl(
            {
                "period": period,
                "sales": sales,
                "food_cost": _money(Decimal(sales) * Decimal(food_rates[index])),
                "labor_cost": _money(Decimal(sales) * Decimal(labor_rates[index])),
                "rent": 38_000_000,
                "utilities": utility_values[index],
                "card_platform_fees": _money(Decimal(sales) * Decimal("0.05")),
                "other_expenses": _money(Decimal(sales) * Decimal("0.045")),
            }
        )
        monthly.append(row)
        budget_sales = [345_000_000, 350_000_000, 352_000_000, 355_000_000, 358_000_000, 360_000_000][index]
        budget = calculate_monthly_pnl(
            {
                "period": period,
                "sales": budget_sales,
                "food_cost": _money(Decimal(budget_sales) * Decimal("0.335")),
                "labor_cost": _money(Decimal(budget_sales) * Decimal("0.275")),
                "rent": 38_000_000,
                "utilities": 20_000_000,
                "card_platform_fees": _money(Decimal(budget_sales) * Decimal("0.05")),
                "other_expenses": _money(Decimal(budget_sales) * Decimal("0.045")),
            }
        )
        budgets.append(budget)
        inflows = _money(Decimal(sales) * Decimal("0.96"))
        outflows = row["operating_expenses"] + 4_000_000
        cash = calculate_cash_flow(beginning_cash, inflows, outflows)
        cash_flows.append({"period": period, **cash})
        beginning_cash = cash["ending_cash"]

    budget_actual = [calculate_budget_actual(actual, budget) for actual, budget in zip(monthly, budgets)]
    return {
        "monthly_pnl": monthly,
        "budgets": budgets,
        "budget_actual": budget_actual,
        "cash_flow": cash_flows,
        "annualized_sales_baseline": 4_200_000_000,
        "allocation_policy_status": POLICY_STATUS,
        "notes": [
            "모든 금액은 담가화로구이 프로토타입 검증용 가상 데이터입니다.",
            "비용 계정 및 부문별 배부 기준은 UNVERIFIED POLICY입니다.",
            "영업이익과 현금흐름은 별도 계산합니다.",
        ],
    }


def _synthetic_menus() -> Dict[str, Any]:
    raw_menus = [
        ("M-001", "담가 갈비", 30_000, 2_650, [("I-MEAT-01", "갈비", 1, 8_500, 1), ("I-SAUCE", "양념·소스", 1, 700, 1), ("I-VEG", "야채", 1, 800, 1), ("I-SIDE", "반찬", 1, 1_000, 1), ("I-CHAR", "숯", 1, 500, 1), ("I-CONS", "소모품", 1, 300, 1), ("I-WASTE", "폐기 허용", 1, 590, 1)]),
        ("M-002", "한우 모둠", 58_000, 1_120, [("I-MEAT-02", "한우", 1, 28_000, 0.97), ("I-SIDE", "반찬", 1, 1_500, 1), ("I-CHAR", "숯", 1, 650, 1)]),
        ("M-003", "돼지갈비", 22_000, 3_100, [("I-MEAT-03", "돼지갈비", 1, 7_600, 0.96), ("I-SAUCE", "양념·소스", 1, 650, 1), ("I-SIDE", "반찬", 1, 850, 1)]),
        ("M-004", "육회", 26_000, 760, [("I-MEAT-04", "육회용 한우", 1, 12_500, 0.98), ("I-SAUCE", "양념", 1, 550, 1)]),
        ("M-005", "갈비탕", 15_000, 2_300, [("I-MEAT-05", "갈비탕 고기", 1, 5_200, 0.94), ("I-SOUP", "육수·부재료", 1, 1_450, 1)]),
        ("M-006", "냉면", 10_000, 1_780, [("I-NOODLE", "면·육수", 1, 2_900, 1)]),
        ("M-007", "된장찌개", 7_000, 980, [("I-SOUP-02", "찌개 재료", 1, 2_100, 1)]),
        ("M-008", "프리미엄 한우", 79_000, 290, [("I-MEAT-06", "프리미엄 한우", 1, 39_000, 0.96), ("I-SIDE", "반찬", 1, 1_600, 1), ("I-CHAR", "숯", 1, 650, 1)]),
    ]
    calculated: List[Dict[str, Any]] = []
    for menu_id, name, price, qty, raw_items in raw_menus:
        calculated.append(
            calculate_menu_cost(
                {
                    "menu_id": menu_id,
                    "menu_name": name,
                    "net_price": price,
                    "sales_quantity": qty,
                    "recipe_version": "SYNTHETIC-V1",
                    "recipe_items": [
                        {
                            "ingredient_id": item_id,
                            "ingredient_name": item_name,
                            "quantity": quantity,
                            "unit_price": unit_price,
                            "yield_rate": yield_rate,
                        }
                        for item_id, item_name, quantity, unit_price, yield_rate in raw_items
                    ],
                }
            )
        )
    quantity_threshold = float(median(item["sales_quantity"] for item in calculated))
    contribution_threshold = float(median(item["unit_contribution"] for item in calculated))
    for item in calculated:
        item["abcd_class"] = classify_menu_abcd(
            item["sales_quantity"],
            item["unit_contribution"],
            quantity_threshold,
            contribution_threshold,
        )
    return {
        "menus": calculated,
        "policy": {
            "status": POLICY_STATUS,
            "sales_threshold_method": "SYNTHETIC_MEDIAN",
            "contribution_threshold_method": "SYNTHETIC_MEDIAN",
            "sales_quantity_threshold": quantity_threshold,
            "unit_contribution_threshold": contribution_threshold,
        },
    }


def _daily_kpis() -> List[Dict[str, str]]:
    return [
        {"order": "1", "name": "일매출", "status": "READY"},
        {"order": "2", "name": "방문팀 수", "status": "PROTOTYPE"},
        {"order": "3", "name": "방문객 수", "status": "READY"},
        {"order": "4", "name": "객단가", "status": "READY"},
        {"order": "5", "name": "테이블당 매출", "status": "PROTOTYPE"},
        {"order": "6", "name": "테이블 회전율", "status": "PROTOTYPE"},
        {"order": "7", "name": "식재료 사용액", "status": "READY"},
        {"order": "8", "name": "근무 인원·근무시간", "status": "PROTOTYPE"},
        {"order": "9", "name": "폐기·서비스 금액", "status": "PROTOTYPE"},
        {"order": "10", "name": "클레임·리뷰", "status": "READY"},
    ]


def _daily_kpi_snapshot() -> List[Dict[str, Any]]:
    sales = 12_400_000
    visiting_teams = 102
    guests = 287
    operating_tables = 48
    food_usage_amount = 4_166_400
    worked_people = 34
    worked_hours = Decimal("258.5")
    waste_amount = 148_000
    service_amount = 139_000
    return [
        {"order": 1, "name": "일매출", "value": sales, "unit": "KRW", "status": "AVAILABLE"},
        {"order": 2, "name": "방문팀 수", "value": visiting_teams, "unit": "TEAM", "status": "AVAILABLE"},
        {"order": 3, "name": "방문객 수", "value": guests, "unit": "PERSON", "status": "AVAILABLE"},
        {"order": 4, "name": "객단가", "value": _money(Decimal(sales) / Decimal(guests)), "unit": "KRW_PER_PERSON", "status": "AVAILABLE"},
        {"order": 5, "name": "테이블당 매출", "value": _money(Decimal(sales) / Decimal(visiting_teams)), "unit": "KRW_PER_TEAM", "status": "AVAILABLE"},
        {"order": 6, "name": "테이블 회전율", "value": round(visiting_teams / operating_tables, 3), "unit": "TURN", "status": "AVAILABLE"},
        {"order": 7, "name": "식재료 사용액", "value": food_usage_amount, "unit": "KRW", "status": "AVAILABLE"},
        {"order": 8, "name": "근무 인원·근무시간", "value": {"people": worked_people, "hours": float(worked_hours)}, "unit": "PERSON_HOUR", "status": "AVAILABLE"},
        {"order": 9, "name": "폐기·서비스 금액", "value": {"waste": waste_amount, "service": service_amount}, "unit": "KRW", "status": "AVAILABLE"},
        {"order": 10, "name": "클레임·리뷰", "value": {"complaints": 1, "reviews": 12}, "unit": "COUNT", "status": "AVAILABLE"},
    ]


def _organization() -> Dict[str, Any]:
    roles = [
        {"role_id": "OWNER", "name": "오너(대표)", "reports_to": None},
        {"role_id": "GENERAL_MANAGER", "name": "총괄점장", "reports_to": "OWNER"},
        {"role_id": "HALL_MANAGER", "name": "홀 매니저", "reports_to": "GENERAL_MANAGER"},
        {"role_id": "KITCHEN_MANAGER", "name": "주방장", "reports_to": "GENERAL_MANAGER"},
        {"role_id": "PURCHASING_MANAGER", "name": "구매·원가관리", "reports_to": "GENERAL_MANAGER"},
        {"role_id": "CUSTOMER_MANAGER", "name": "예약·고객관리", "reports_to": "GENERAL_MANAGER"},
        {"role_id": "TEAM_LEAD", "name": "파트장", "reports_to": "FUNCTION_MANAGER"},
        {"role_id": "EMPLOYEE", "name": "직원(정직원·파트타임)", "reports_to": "TEAM_LEAD"},
    ]
    scorecard = [
        ("매출", 20),
        ("영업이익", 25),
        ("식재료 원가율", 15),
        ("인건비율", 15),
        ("고객 만족·리뷰", 10),
        ("직원 이직률", 5),
        ("클레임", 5),
        ("재고 차이율", 5),
    ]
    return {
        "roles": roles,
        "raci_policy_status": POLICY_STATUS,
        "raci_assignments": [
            {"process": "일일 경영판 검토", "responsible": "GENERAL_MANAGER", "accountable": "OWNER", "consulted": ["HALL_MANAGER", "KITCHEN_MANAGER"], "informed": ["TEAM_LEAD"]},
            {"process": "식재료 원가 검토", "responsible": "PURCHASING_MANAGER", "accountable": "GENERAL_MANAGER", "consulted": ["KITCHEN_MANAGER"], "informed": ["OWNER"]},
            {"process": "고객 클레임 조치", "responsible": "CUSTOMER_MANAGER", "accountable": "GENERAL_MANAGER", "consulted": ["HALL_MANAGER"], "informed": ["OWNER"]},
        ],
        "approval_policies": [
            {"policy_id": "AP-SYN-001", "action_type": "PURCHASE", "rule": "금액 구간별 이중승인 검증", "status": POLICY_STATUS, "automatic_execution": False, "self_approval_allowed": False},
            {"policy_id": "AP-SYN-002", "action_type": "CONTRACT", "rule": "계약·만기 검토 후 대표 승인", "status": POLICY_STATUS, "automatic_execution": False, "self_approval_allowed": False},
            {"policy_id": "AP-SYN-003", "action_type": "MENU_PRICE", "rule": "가격 변경 전 대표 승인", "status": POLICY_STATUS, "automatic_execution": False, "self_approval_allowed": False},
        ],
        "manager_scorecard": [{"metric": metric, "weight": weight} for metric, weight in scorecard],
        "scorecard_policy_status": POLICY_STATUS,
        "scorecard_total_weight": sum(weight for _, weight in scorecard),
        "automated_employment_decisions": False,
    }


def _standards_and_actions() -> Dict[str, Any]:
    sops = [
        {
            "sop_id": "SOP-INV-003",
            "title": "재고 차이 확인 절차",
            "linked_rule_ids": ["R-INV-01"],
            "version": "SYNTHETIC-V1",
            "owner_role": "PURCHASING_MANAGER",
            "checklist": ["재고 재계량", "입고량 확인", "POS 판매량 확인", "서비스 기록 확인", "폐기 기록 확인", "직원식 기록 확인", "단위 확인", "원인 기록"],
        },
        {
            "sop_id": "SOP-KIT-001",
            "title": "주방 표준 조리 절차",
            "linked_rule_ids": ["R-FC-01", "R-WST-01"],
            "version": "SYNTHETIC-V1",
            "owner_role": "KITCHEN_MANAGER",
            "checklist": ["고기 규격·1인분 중량 확인", "숙성 시간·보관 확인", "양념 배합 확인", "반찬 정량·플레이팅 확인", "숯 상태·화력 확인", "폐기 기록"],
        },
        {
            "sop_id": "SOP-HALL-001",
            "title": "홀 서비스 표준 절차",
            "linked_rule_ids": ["R-CUS-01"],
            "version": "SYNTHETIC-V1",
            "owner_role": "HALL_MANAGER",
            "checklist": ["테이블 세팅", "주문 확인", "서빙 순서", "테이블 회전 기록", "컴플레인 대응 기록", "마감 확인"],
        },
    ]
    actions = [
        {"action_id": "ACT-SYN-001", "title": "재고 차이 재계량 및 기록 대사", "source_rule_id": "R-INV-01", "sop_id": "SOP-INV-003", "owner_role": "PURCHASING_MANAGER", "priority": "CRITICAL", "status": "IN_PROGRESS", "due_date": "2026-09-02", "evidence_id": "EV-ACT-SYN-001"},
        {"action_id": "ACT-SYN-002", "title": "갈비 Recipe 표준량 검증", "source_rule_id": "R-FC-01", "sop_id": "SOP-KIT-001", "owner_role": "KITCHEN_MANAGER", "priority": "HIGH", "status": "OPEN", "due_date": "2026-09-05", "evidence_id": "EV-ACT-SYN-002"},
        {"action_id": "ACT-SYN-003", "title": "클레임 응대 기록 검토", "source_rule_id": "R-CUS-01", "sop_id": "SOP-HALL-001", "owner_role": "CUSTOMER_MANAGER", "priority": "MEDIUM", "status": "VERIFIED", "due_date": "2026-08-31", "evidence_id": "EV-ACT-SYN-003"},
    ]
    return {
        "sops": sops,
        "actions": actions,
        "action_state_machine": ["OPEN", "IN_PROGRESS", "CLOSED", "VERIFIED"],
        "automatic_execution_enabled": False,
    }


def build_management_prototype() -> Dict[str, Any]:
    finance = _synthetic_finance()
    menu_engineering = _synthetic_menus()
    organization = _organization()
    standards = _standards_and_actions()
    latest_pnl = finance["monthly_pnl"][-1]
    action_counts: Dict[str, int] = {}
    for action in standards["actions"]:
        action_counts[action["status"]] = action_counts.get(action["status"], 0) + 1
    review = {
        "period": latest_pnl["period"],
        "status": "REVIEW_REQUIRED",
        "sales": latest_pnl["sales"],
        "operating_profit": latest_pnl["operating_profit"],
        "operating_margin": latest_pnl["operating_margin"],
        "food_cost_ratio": latest_pnl["food_cost_ratio"],
        "labor_ratio": latest_pnl["labor_ratio"],
        "menu_abcd_counts": {
            grade: sum(1 for menu in menu_engineering["menus"] if menu["abcd_class"] == grade)
            for grade in ("A", "B", "C", "D")
        },
        "action_counts": action_counts,
        "top_actions": [action["title"] for action in standards["actions"] if action["status"] != "VERIFIED"],
        "human_approval_required": True,
        "ai_calculated_numbers": False,
        "management_brief": {
            "status": "REVIEW_REQUIRED",
            "provider": "deterministic-prototype",
            "executive_summary": (
                f"{latest_pnl['period']} 담가화로구이 Synthetic 경영검토에서 "
                f"매출 {latest_pnl['sales']:,}원, 영업이익 {latest_pnl['operating_profit']:,}원이 계산되었습니다."
            ),
            "findings": [
                "월 손익·현금흐름·메뉴 원가·조치 현황을 함께 검토해야 합니다.",
                "모든 수치는 실제 매장 실적이 아닌 결정론적 Synthetic Facts입니다.",
            ],
            "recommended_actions": [action["title"] for action in standards["actions"] if action["status"] != "VERIFIED"],
            "human_approval_required": True,
        },
    }
    payload: Dict[str, Any] = {
        "brand_name": BRAND_NAME,
        "prototype_version": PROTOTYPE_VERSION,
        "dataset_type": DATASET_TYPE,
        "data_disclosure": "SYNTHETIC · 실제 담가화로구이 매장 데이터 아님",
        "policy_status": POLICY_STATUS,
        "purpose": "실제 사용 전 경영체계 검증용 프로토타입",
        "daily_kpis": _daily_kpis(),
        "daily_kpi_snapshot": _daily_kpi_snapshot(),
        "finance": finance,
        "menu_engineering": menu_engineering,
        "organization": organization,
        "standards": standards,
        "monthly_review": review,
        "human_approval": {
            "required": True,
            "authentication_status": "SIMULATED",
            "automatic_price_change": False,
            "automatic_ordering": False,
            "automatic_employment_action": False,
        },
    }
    payload["content_sha256"] = sha256(repr(payload).encode("utf-8")).hexdigest()
    return payload


def get_synthetic_actions() -> Iterable[Dict[str, Any]]:
    return build_management_prototype()["standards"]["actions"]
