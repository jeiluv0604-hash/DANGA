# -*- coding: utf-8 -*-
import re
from typing import List, Set, Tuple
from domains.analyst.schemas import AnalystContext, StructuredAnalystOutput

PROHIBITED_WORDS = [
    '절도', '횡령', '도난', '훔침', '빼돌림',
    '직원 과실', '직원 실수', '직원 탓', '근무 태만',
    '고의 누락', '부정행위', '부정 결제', '범죄',
    '직원 해고', '감원', '인원 감축', '해고', '임금 삭감', '처벌', '권고사직', '징계',
    'theft', 'embezzlement', 'fraud', 'fire employee'
]

class SafetyValidator:
    """
    SafetyValidator (v1.1):
    Enforces AI-01 ~ AI-07 Golden Principles + Semantic Numeric Grounding + Claim Evidence Binding.
    """

    @staticmethod
    def validate(context: AnalystContext, output: StructuredAnalystOutput) -> Tuple[bool, List[str]]:
        reasons = []

        # 1. Check DATA_INCOMPLETE block
        if not context.ai_eligible or context.data_status == "DATA_INCOMPLETE":
            if output.status != "BLOCKED":
                reasons.append("DATA_INCOMPLETE requires status='BLOCKED'")

        # 2. Check Synthetic Disclosure
        if context.dataset_type == "SYNTHETIC" and output.dataset_disclosure != "SYNTHETIC":
            reasons.append("Missing or mismatched synthetic dataset disclosure")

        # 3. Check Prohibited Accusations / Actions
        all_text = " ".join([
            output.executive_summary,
            " ".join(f.finding for f in output.findings),
            " ".join(f"{c.hypothesis} {c.basis}" for c in output.possible_causes),
            " ".join(a.action for a in output.recommended_actions)
        ])
        for word in PROHIBITED_WORDS:
            if word in all_text:
                reasons.append(f"Prohibited accusation or punitive term detected: '{word}'")

        # If status is BLOCKED or PROVIDER_UNAVAILABLE or ERROR, bypass finding deep checks
        if output.status in ["BLOCKED", "PROVIDER_UNAVAILABLE", "ERROR"]:
            if output.status == "BLOCKED" and context.data_status != "DATA_INCOMPLETE" and context.ai_eligible:
                reasons.append("Output marked BLOCKED but data status is OK and AI is eligible")
            return len(reasons) == 0, reasons

        # 4. Check approval_required on all recommended actions
        for i, action in enumerate(output.recommended_actions):
            if not action.approval_required:
                reasons.append(f"Action #{i+1} has approval_required=False (human approval mandatory)")

        # 5. Check Evidence grounding
        valid_evidence_ids = {e.get("evidence_id") for e in context.evidence if e.get("evidence_id")}
        for a in context.alerts:
            if a.get("evidence_id"):
                valid_evidence_ids.add(a.get("evidence_id"))

        for i, finding in enumerate(output.findings):
            if not finding.evidence_ids:
                reasons.append(f"Finding #{i+1} has no evidence_id linkage")
            else:
                for eid in finding.evidence_ids:
                    if valid_evidence_ids and eid not in valid_evidence_ids:
                        reasons.append(f"Finding #{i+1} references nonexistent evidence_id: '{eid}'")

        for i, cause in enumerate(output.possible_causes):
            if not cause.evidence_ids:
                reasons.append(f"Possible cause #{i+1} has no evidence_id linkage")

        for i, action in enumerate(output.recommended_actions):
            if not action.evidence_ids:
                reasons.append(f"Recommended action #{i+1} has no evidence_id linkage")

        # 6. SEMANTIC NUMERIC GROUNDING & FACT REF VALIDATION (GROUND-01 ~ GROUND-06)
        for i, finding in enumerate(output.findings):
            for j, ref in enumerate(finding.fact_refs):
                # 6.1 Check metric existence
                if ref.metric not in context.facts:
                    reasons.append(f"Finding #{i+1} fact_ref #{j+1} references nonexistent metric: '{ref.metric}'")
                    continue
                
                # 6.2 Check business_date match (GROUND-03, GROUND-06)
                if ref.business_date != context.business_date:
                    reasons.append(f"Finding #{i+1} fact_ref #{j+1} business_date mismatch: claimed '{ref.business_date}', expected '{context.business_date}'")
                
                # 6.3 Check semantic value swap (GROUND-01, GROUND-02, GROUND-05)
                actual_val = context.facts.get(ref.metric)
                if actual_val is not None and isinstance(actual_val, (int, float)):
                    if abs(actual_val - ref.value) > 1e-4:
                        reasons.append(f"Finding #{i+1} semantic swap / numeric mismatch for '{ref.metric}': claimed {ref.value}, actual {actual_val}")
                
                # 6.4 Check evidence_id binding (GROUND-04)
                if valid_evidence_ids and ref.evidence_id not in valid_evidence_ids:
                    reasons.append(f"Finding #{i+1} fact_ref #{j+1} references invalid evidence_id: '{ref.evidence_id}'")

        # 7. Check Numeric Hallucination (Strict)
        if output.status == "READY":
            valid_numbers_str = set()
            for k, v in context.facts.items():
                if v is not None and isinstance(v, (int, float)):
                    valid_numbers_str.add(str(round(v, 2)))
                    valid_numbers_str.add(str(round(v, 4)))
                    valid_numbers_str.add(str(int(v)))
                    valid_numbers_str.add(f"{v:,.0f}")
                    if 0 < v < 1:
                        valid_numbers_str.add(f"{v * 100:.1f}")
                        valid_numbers_str.add(f"{v * 100:.0f}")

            for a in context.alerts:
                for fld in ["actual_value", "threshold_value", "comparison"]:
                    val = a.get(fld)
                    if val is not None:
                        val_str = str(val)
                        valid_numbers_str.add(val_str)
                        for tok in re.findall(r'\d+(?:\.\d+)?', val_str):
                            valid_numbers_str.add(tok)
                            try:
                                valid_numbers_str.add(f"{float(tok):.1f}")
                                valid_numbers_str.add(f"{float(tok):.0f}")
                            except:
                                pass

            # Common legitimate constants allowed in explanations
            allowed_constants = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '14', '30', '33', '35', '38', '39', '40', '100'}
            valid_numbers_str.update(allowed_constants)

            # Date parts
            if context.business_date:
                for part in context.business_date.split('-'):
                    valid_numbers_str.add(part)
                    valid_numbers_str.add(str(int(part)))

            # Extract numeric tokens from findings text
            for finding in output.findings:
                tokens = re.findall(r'\d+(?:\.\d+)?', finding.finding)
                for tok in tokens:
                    if tok not in valid_numbers_str:
                        match = False
                        try:
                            f_tok = float(tok)
                            for val in context.facts.values():
                                if isinstance(val, (int, float)) and abs(val - f_tok) < 1e-4:
                                    match = True
                                    break
                        except:
                            pass
                        if not match:
                            reasons.append(f"Hallucinated or ungrounded numeric token in finding: '{tok}'")

        is_valid = len(reasons) == 0
        return is_valid, reasons

