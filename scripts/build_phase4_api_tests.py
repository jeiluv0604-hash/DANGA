# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print('Wrote:', path)

write_file('tests/analyst/test_analyst_api.py', """# -*- coding: utf-8 -*-
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

class TestAnalystAPI:

    def test_generate_and_get_daily_brief(self):
        \"\"\"Test generating and getting daily brief via REST API\"\"\"
        res = client.post("/api/v1/analyst/daily/2026-06-12")
        assert res.status_code == 200
        data = res.json()
        assert data["business_date"] == "2026-06-12"
        assert data["status"] in ["REVIEW_REQUIRED", "READY"]
        assert len(data["findings"]) >= 1
        assert data["approval_disclaimer"] == "DEVELOPMENT HUMAN APPROVAL SIMULATION"

        brief_id = data["brief_id"]
        # GET by date
        res_get = client.get("/api/v1/analyst/daily/2026-06-12")
        assert res_get.status_code == 200
        assert res_get.json()["brief_id"] == brief_id

        # GET by ID
        res_id = client.get(f"/api/v1/analyst/briefs/{brief_id}")
        assert res_id.status_code == 200
        assert res_id.json()["brief_id"] == brief_id

    def test_ai_014_human_approve_workflow(self):
        \"\"\"AI-TEST-014: Human approve -> REVIEW_REQUIRED -> APPROVED + Audit Log\"\"\"
        res_gen = client.post("/api/v1/analyst/daily/2026-06-12")
        brief_id = res_gen.json()["brief_id"]

        # Approve brief
        res_app = client.post(
            f"/api/v1/analyst/briefs/{brief_id}/approve",
            json={"reviewer_role": "CEO", "comment": "승인 완료: 파트타임 인력 재배치 지시"}
        )
        assert res_app.status_code == 200
        data = res_app.json()
        assert data["status"] == "APPROVED"
        assert data["reviewed_at"] is not None

        # Check Audit Log
        res_audit = client.get(f"/api/v1/analyst/briefs/{brief_id}/audit")
        assert res_audit.status_code == 200
        logs = res_audit.json()
        assert len(logs) >= 1
        assert logs[-1]["new_status"] == "APPROVED"
        assert logs[-1]["actor_role"] == "CEO"

    def test_ai_015_human_reject_workflow(self):
        \"\"\"AI-TEST-015: Human reject -> REVIEW_REQUIRED -> REJECTED + Audit Log\"\"\"
        res_gen = client.post("/api/v1/analyst/daily/2026-07-08")
        brief_id = res_gen.json()["brief_id"]

        # Reject brief
        res_rej = client.post(
            f"/api/v1/analyst/briefs/{brief_id}/reject",
            json={"reviewer_role": "GENERAL_MANAGER", "comment": "반려: 재측정 결과 이상 없음 확인"}
        )
        assert res_rej.status_code == 200
        data = res_rej.json()
        assert data["status"] == "REJECTED"
        assert data["reviewed_at"] is not None

        # Check Audit Log
        res_audit = client.get(f"/api/v1/analyst/briefs/{brief_id}/audit")
        assert res_audit.status_code == 200
        logs = res_audit.json()
        assert any(l["new_status"] == "REJECTED" for l in logs)

    def test_data_incomplete_api_response(self):
        \"\"\"Verify 2026-08-21 returns deterministic BLOCKED response\"\"\"
        res = client.post("/api/v1/analyst/daily/2026-08-21")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "BLOCKED"
        assert "Food_Cost" in data["executive_summary"] or "누락" in data["executive_summary"]
""")

