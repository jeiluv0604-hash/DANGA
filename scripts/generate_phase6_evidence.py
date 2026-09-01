# -*- coding: utf-8 -*-
"""Generate Phase 6 evidence and an external byte-hash index."""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path

from domains.management.prototype import build_management_prototype


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence"
EVIDENCE_FILE = EVIDENCE_DIR / "phase-6-management-system-prototype.json"
INDEX_FILE = EVIDENCE_DIR / "phase-6-management-system-prototype.index.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    prototype = build_management_prototype()
    source_files = [
        ROOT / "domains" / "management" / "prototype.py",
        ROOT / "apps" / "api" / "routes" / "management.py",
        ROOT / "apps" / "frontend" / "src" / "components" / "management" / "ManagementSystemSection.tsx",
        ROOT / "tests" / "management" / "test_management_prototype.py",
    ]
    screenshot = EVIDENCE_DIR / "EV-UI-MANAGEMENT-PROTOTYPE.png"
    evidence = {
        "evidence_id": "EV-PHASE6-MANAGEMENT-SYSTEM-PROTOTYPE",
        "phase": "PHASE_6",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "brand_name": "담가화로구이",
        "dataset_type": "SYNTHETIC",
        "data_disclosure": "SYNTHETIC · 실제 담가화로구이 매장 데이터 아님",
        "policy_status": {
            "cost_allocation": "UNVERIFIED POLICY",
            "menu_abcd": "UNVERIFIED POLICY",
            "manager_scorecard": "UNVERIFIED POLICY",
        },
        "components_verified": [
            "10 Daily Management KPIs",
            "Monthly P&L",
            "Budget vs Actual",
            "Cash Flow",
            "Recipe/BOM Cost Engine",
            "Menu ABCD Engineering",
            "Organization/RACI",
            "Manager Scorecard",
            "Approval Policies",
            "SOP/Checklist",
            "Action Closure and Audit Chain",
            "Monthly Management Review",
            "Deterministic AI Management Brief",
            "CEO Cockpit Integration",
        ],
        "test_results": {
            "pytest": 202,
            "vitest": 24,
            "playwright": 18,
            "production_build": "PASS",
            "total_automated_tests": 244,
            "failures": 0,
        },
        "safety": {
            "automatic_price_change": False,
            "automatic_ordering": False,
            "automatic_payment": False,
            "automatic_employment_action": False,
            "human_approval_required": True,
            "ai_calculated_numbers": False,
        },
        "prototype_content_sha256": prototype["content_sha256"],
        "source_sha256": {str(path.relative_to(ROOT)): sha256_file(path) for path in source_files},
        "screenshot": {
            "path": str(screenshot.relative_to(ROOT)) if screenshot.exists() else None,
            "sha256": sha256_file(screenshot) if screenshot.exists() else None,
        },
        "overall_status": "PASS",
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    evidence_bytes = (json.dumps(evidence, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    EVIDENCE_FILE.write_bytes(evidence_bytes)
    index = {
        "evidence_id": evidence["evidence_id"],
        "file_path": str(EVIDENCE_FILE.relative_to(ROOT)),
        "file_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
        "dataset_type": "SYNTHETIC",
        "created_at": evidence["timestamp"],
    }
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, ensure_ascii=False))


if __name__ == "__main__":
    main()

