# -*- coding: utf-8 -*-
import pytest
from domains.analyst.context_builder import AnalystContextBuilder
from domains.analyst.safety import SafetyValidator
from domains.analyst.schemas import (
    AnalystContext,
    StructuredAnalystOutput,
    FindingItem,
    PossibleCauseItem,
    RecommendedActionItem,
    FactRef
)

class TestSemanticGrounding:
    @pytest.fixture
    def base_context(self) -> AnalystContext:
        return AnalystContextBuilder.build_context(
            business_date="2026-06-12",
            facts_dict={
                "sales": 13092000,
                "labor_cost": 4648000,
                "labor_ratio": 0.355,
                "food_cost": 4401000,
                "food_cost_ratio": 0.336,
                "inventory_variance_kg": -0.9
            },
            alerts_list=[
                {"rule_id": "R-LAB-01", "severity": "HIGH", "actual_value": "35.5%", "threshold_value": "33.0%", "evidence_id": "EV-ALT-LAB-01"}
            ],
            evidence_list=[{"evidence_id": "EV-ALT-LAB-01"}]
        )

    def _build_test_output(self, findings: list) -> StructuredAnalystOutput:
        return StructuredAnalystOutput(
            status="READY",
            business_date="2026-06-12",
            dataset_disclosure="SYNTHETIC",
            executive_summary="테스트 요약",
            findings=findings,
            possible_causes=[
                PossibleCauseItem(
                    hypothesis="가설",
                    confidence="HIGH",
                    basis="근거",
                    evidence_ids=["EV-ALT-LAB-01"]
                )
            ],
            recommended_actions=[
                RecommendedActionItem(
                    action="조치",
                    owner_role="GENERAL_MANAGER",
                    priority="HIGH",
                    approval_required=True,
                    evidence_ids=["EV-ALT-LAB-01"]
                )
            ]
        )

    def test_ground_01_sales_value_claimed_as_labor_cost(self, base_context):
        # Sales is 13,092,000, but claimed as labor_cost
        finding = FindingItem(
            finding="인건비는 13,092,000원입니다.",
            severity="HIGH",
            rule_id="R-LAB-01",
            evidence_ids=["EV-ALT-LAB-01"],
            fact_refs=[
                FactRef(
                    metric="labor_cost",
                    value=13092000.0,
                    business_date="2026-06-12",
                    evidence_id="EV-ALT-LAB-01"
                )
            ]
        )
        output = self._build_test_output([finding])
        is_safe, reasons = SafetyValidator.validate(base_context, output)
        assert not is_safe
        assert any("semantic swap" in r or "numeric mismatch" in r for r in reasons)

    def test_ground_02_labor_ratio_claimed_as_food_cost_ratio(self, base_context):
        # labor_ratio is 0.355, claimed as food_cost_ratio (actual 0.336)
        finding = FindingItem(
            finding="식재료 원가율이 35.5%로 측정되었습니다.",
            severity="HIGH",
            rule_id="R-LAB-01",
            evidence_ids=["EV-ALT-LAB-01"],
            fact_refs=[
                FactRef(
                    metric="food_cost_ratio",
                    value=0.355,
                    business_date="2026-06-12",
                    evidence_id="EV-ALT-LAB-01"
                )
            ]
        )
        output = self._build_test_output([finding])
        is_safe, reasons = SafetyValidator.validate(base_context, output)
        assert not is_safe
        assert any("semantic swap" in r for r in reasons)

    def test_ground_03_cross_date_value_claimed_as_today(self, base_context):
        # Claimed date is 2026-06-11 instead of 2026-06-12
        finding = FindingItem(
            finding="인건비율이 35.5%입니다.",
            severity="HIGH",
            rule_id="R-LAB-01",
            evidence_ids=["EV-ALT-LAB-01"],
            fact_refs=[
                FactRef(
                    metric="labor_ratio",
                    value=0.355,
                    business_date="2026-06-11",
                    evidence_id="EV-ALT-LAB-01"
                )
            ]
        )
        output = self._build_test_output([finding])
        is_safe, reasons = SafetyValidator.validate(base_context, output)
        assert not is_safe
        assert any("business_date mismatch" in r for r in reasons)

    def test_ground_04_wrong_evidence_id_binding(self, base_context):
        # Valid metric and value, but referencing nonexistent/wrong evidence_id
        finding = FindingItem(
            finding="인건비율이 35.5%입니다.",
            severity="HIGH",
            rule_id="R-LAB-01",
            evidence_ids=["EV-NONEXISTENT-999"],
            fact_refs=[
                FactRef(
                    metric="labor_ratio",
                    value=0.355,
                    business_date="2026-06-12",
                    evidence_id="EV-NONEXISTENT-999"
                )
            ]
        )
        output = self._build_test_output([finding])
        is_safe, reasons = SafetyValidator.validate(base_context, output)
        assert not is_safe
        assert any("nonexistent evidence_id" in r or "invalid evidence_id" in r for r in reasons)

    def test_ground_05_nonexistent_metric_name(self, base_context):
        finding = FindingItem(
            finding="가상 지표 수치 100",
            severity="HIGH",
            rule_id="R-LAB-01",
            evidence_ids=["EV-ALT-LAB-01"],
            fact_refs=[
                FactRef(
                    metric="hallucinated_metric_x",
                    value=100.0,
                    business_date="2026-06-12",
                    evidence_id="EV-ALT-LAB-01"
                )
            ]
        )
        output = self._build_test_output([finding])
        is_safe, reasons = SafetyValidator.validate(base_context, output)
        assert not is_safe
        assert any("nonexistent metric" in r for r in reasons)

    def test_ground_06_correct_fact_ref_passes_validation(self, base_context):
        finding = FindingItem(
            finding="인건비율이 35.5%로 관리 기준을 초과했습니다.",
            severity="HIGH",
            rule_id="R-LAB-01",
            evidence_ids=["EV-ALT-LAB-01"],
            fact_refs=[
                FactRef(
                    metric="labor_ratio",
                    value=0.355,
                    business_date="2026-06-12",
                    evidence_id="EV-ALT-LAB-01"
                )
            ]
        )
        output = self._build_test_output([finding])
        is_safe, reasons = SafetyValidator.validate(base_context, output)
        assert is_safe
        assert len(reasons) == 0

