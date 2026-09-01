# -*- coding: utf-8 -*-
from typing import Dict, Any, List, Optional
from domains.analyst.schemas import AnalystContext

class AnalystContextBuilder:
    """
    AnalystContextBuilder:
    Reads ONLY stored Facts, Alerts, and Evidence from database/domain models.
    NEVER references golden test labels (Expected_Anomaly_ID, GA-001, ADV-001, Ground_Truth).
    """

    @staticmethod
    def build_context(
        business_date: str,
        facts_dict: Optional[Dict[str, Any]],
        alerts_list: Optional[List[Dict[str, Any]]],
        evidence_list: Optional[List[Dict[str, Any]]] = None,
        data_status: str = "OK",
        ai_eligible: bool = True,
        untrusted_text_data: Optional[List[str]] = None,
        dataset_type: str = "SYNTHETIC"
    ) -> AnalystContext:
        safe_facts = {}
        if facts_dict:
            for k, v in facts_dict.items():
                if k not in ['expected_anomaly_id', 'golden_anomaly', 'ground_truth']:
                    safe_facts[k] = v

        safe_alerts = []
        if alerts_list:
            for alert in alerts_list:
                safe_alerts.append({
                    "rule_id": alert.get("rule_id"),
                    "severity": alert.get("severity"),
                    "status": alert.get("status"),
                    "actual_value": str(alert.get("actual") if alert.get("actual") is not None else alert.get("actual_value")),
                    "threshold_value": str(alert.get("threshold") if alert.get("threshold") is not None else alert.get("threshold_value")),
                    "comparison": alert.get("comparison"),
                    "evidence_id": alert.get("evidence_id")
                })

        safe_evidence = []
        if evidence_list:
            for ev in evidence_list:
                safe_evidence.append({
                    "evidence_id": ev.get("evidence_id"),
                    "rule_id": ev.get("rule_id"),
                    "file_sha256": ev.get("file_sha256"),
                    "dataset_sha256": ev.get("dataset_sha256")
                })

        safe_untrusted = []
        if untrusted_text_data:
            for item in untrusted_text_data:
                if isinstance(item, str):
                    wrapped = f"<UNTRUSTED_BUSINESS_DATA>{item[:500]}</UNTRUSTED_BUSINESS_DATA>"
                    safe_untrusted.append(wrapped)

        return AnalystContext(
            business_date=business_date,
            dataset_type=dataset_type,
            data_status=data_status,
            ai_eligible=ai_eligible,
            facts=safe_facts,
            alerts=safe_alerts,
            evidence=safe_evidence,
            untrusted_text_data=safe_untrusted,
            constraints={
                "no_new_numbers": True,
                "no_accusations": True,
                "human_approval_required": True,
                "synthetic_disclosure": True
            }
        )
