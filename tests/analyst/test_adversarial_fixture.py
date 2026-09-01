# -*- coding: utf-8 -*-
import pytest
from domains.analyst.context_builder import AnalystContextBuilder
from domains.analyst.deterministic_brief import DeterministicAnalyst
from domains.analyst.safety import SafetyValidator
from domains.analyst.providers.mock_provider import MockAnalystProvider

class TestAdversarialFixture:
    """
    Adversarial fixture tests using arbitrary future dates (2026-10-15, 2026-11-01)
    to guarantee zero golden date dependency.
    """

    def test_adv_date_01_labor_spike_20261015(self):
        ctx = AnalystContextBuilder.build_context(
            business_date="2026-10-15",
            facts_dict={"sales": 15000000, "labor_ratio": 0.362},
            alerts_list=[{"rule_id": "R-LAB-01", "severity": "HIGH", "actual_value": "36.2%", "threshold_value": "33.0%", "evidence_id": "EV-ADV-1015"}],
            evidence_list=[{"evidence_id": "EV-ADV-1015"}]
        )
        provider = MockAnalystProvider()
        output = provider.generate_brief(ctx)
        is_safe, reasons = SafetyValidator.validate(ctx, output)
        assert is_safe
        assert output.status == "READY"
        assert output.business_date == "2026-10-15"

    def test_adv_date_02_inventory_variance_20261101(self):
        ctx = AnalystContextBuilder.build_context(
            business_date="2026-11-01",
            facts_dict={"sales": 18000000, "inventory_variance_kg": -12.4},
            alerts_list=[{"rule_id": "R-INV-01", "severity": "CRITICAL", "actual_value": "-12.4kg", "threshold_value": "-5.0kg", "evidence_id": "EV-ADV-1101"}],
            evidence_list=[{"evidence_id": "EV-ADV-1101"}]
        )
        provider = MockAnalystProvider()
        output = provider.generate_brief(ctx)
        is_safe, reasons = SafetyValidator.validate(ctx, output)
        assert is_safe
        assert output.status == "READY"
        assert output.business_date == "2026-11-01"

    def test_adv_date_03_data_incomplete_blocked_20261205(self):
        ctx = AnalystContextBuilder.build_context(
            business_date="2026-12-05",
            facts_dict={"sales": 14000000, "food_cost": None},
            alerts_list=[{"rule_id": "R-DQ-01", "severity": "CRITICAL", "actual_value": ["Food_Cost"], "threshold_value": "Valid", "evidence_id": "EV-ADV-1205"}],
            evidence_list=[{"evidence_id": "EV-ADV-1205"}],
            data_status="DATA_INCOMPLETE",
            ai_eligible=False
        )
        provider = MockAnalystProvider()
        output = provider.generate_brief(ctx)
        assert output.status == "BLOCKED"
        is_safe, reasons = SafetyValidator.validate(ctx, output)
        assert is_safe

