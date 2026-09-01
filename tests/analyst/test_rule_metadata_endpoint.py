# -*- coding: utf-8 -*-
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from domains.rules import RULES

client = TestClient(app)

class TestRuleMetadataEndpoint:
    def test_get_rules_metadata_matches_domain_rules(self):
        response = client.get("/api/v1/rules/metadata")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(RULES)
        
        rule_map = {r["rule_id"]: r for r in data}
        
        # Verify specific critical rule thresholds
        assert rule_map["R-FC-01"]["threshold"] == 0.39
        assert rule_map["R-INV-01"]["threshold"] == -5.0
        assert rule_map["R-WST-01"]["threshold"] == 0.05
        assert rule_map["R-LAB-01"]["threshold"] == 0.33

