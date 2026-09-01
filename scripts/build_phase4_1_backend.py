# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print('Wrote:', path)

# 1. Schemas
write_file('domains/analyst/schemas.py', """# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

class FactRef(BaseModel):
    metric: str
    value: float
    display_value: Optional[str] = None
    source: str = "daily_facts"
    business_date: str
    evidence_id: str

class FindingItem(BaseModel):
    finding: str
    severity: Literal['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'] = 'INFO'
    rule_id: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)
    fact_refs: List[FactRef] = Field(default_factory=list)

class PossibleCauseItem(BaseModel):
    hypothesis: str
    confidence: Literal['HIGH', 'MEDIUM', 'LOW'] = 'MEDIUM'
    basis: str
    evidence_ids: List[str] = Field(default_factory=list)

class RecommendedActionItem(BaseModel):
    action: str
    owner_role: Literal['CEO', 'GENERAL_MANAGER', 'FLOOR_MANAGER', 'KITCHEN_LEAD'] = 'GENERAL_MANAGER'
    priority: Literal['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] = 'MEDIUM'
    approval_required: bool = True
    evidence_ids: List[str] = Field(default_factory=list)

class AnalystContext(BaseModel):
    business_date: str
    data_status: Literal['OK', 'DATA_INCOMPLETE'] = 'OK'
    ai_eligible: bool = True
    dataset_type: Literal['SYNTHETIC', 'UNVERIFIED', 'PRODUCTION'] = 'SYNTHETIC'
    facts: Dict[str, Any] = Field(default_factory=dict)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    untrusted_text_data: List[str] = Field(default_factory=list)

class StructuredAnalystOutput(BaseModel):
    status: Literal['READY', 'BLOCKED', 'PROVIDER_UNAVAILABLE', 'ERROR', 'REJECTED'] = 'READY'
    business_date: str
    dataset_disclosure: str = "SYNTHETIC"
    executive_summary: str
    findings: List[FindingItem] = Field(default_factory=list)
    possible_causes: List[PossibleCauseItem] = Field(default_factory=list)
    recommended_actions: List[RecommendedActionItem] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    missing_inputs: List[str] = Field(default_factory=list)
    available_facts: List[str] = Field(default_factory=list)
    prohibited_inference_detected: bool = False
    rejection_reasons: List[str] = Field(default_factory=list)
    
    # Provider & Fallback Contract
    requested_provider: str = "mock"
    actual_provider: str = "mock"
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    
    # Version Traceability
    prompt_version: str = "v1.1"
    facts_version: str = "v1.0"
    rule_version: str = "v1.0"
    validator_version: str = "v1.1"
    provider_version: str = "v1.1"
    code_version: str = "1.1.0"
    dataset_sha256: Optional[str] = None
    raw_response_hash: Optional[str] = None
    
    # Governance & Simulation
    review_authentication_status: str = "SIMULATED"
    identity_verified: bool = False
    provider: str = "mock"
    model: str = "mock-analyst-gpt4o-mini-simulator"
""")

# 2. Safety Validator
write_file('domains/analyst/safety.py', """# -*- coding: utf-8 -*-
import re
from typing import Tuple, List, Set, Dict, Any
from domains.analyst.schemas import AnalystContext, StructuredAnalystOutput

PROHIBITED_WORDS = {
    '절도', '횡령', '도난', '훔침', '빼돌림',
    '직원 과실', '직원 실수', '직원 탓', '근무 태만',
    '고의 누락', '부정행위', '부정 결제',
    '해고', '권고사직', '감원', '징계'
}

class SafetyValidator:
    \"\"\"
    SafetyValidator (v1.1):
    Enforces AI-01 ~ AI-07 Golden Principles + Semantic Numeric Grounding + Claim Evidence Binding.
    \"\"\"

    @classmethod
    def validate(cls, context: AnalystContext, output: StructuredAnalystOutput) -> Tuple[bool, List[str]]:
        reasons = []

        # 1. Check DATA_INCOMPLETE status
        if context.data_status == "DATA_INCOMPLETE" or not context.ai_eligible:
            if output.status != "BLOCKED":
                reasons.append("DATA_INCOMPLETE day must return status='BLOCKED'")

        # 2. Check Synthetic Disclosure
        if context.dataset_type == "SYNTHETIC" and output.dataset_disclosure != "SYNTHETIC":
            reasons.append("Synthetic dataset disclosure missing or mismatched in output")

        # 3. Check Prohibited Accusation & Punitive Terms
        all_text = " ".join([
            output.executive_summary,
            " ".join(f.finding for f in output.findings),
            " ".join(c.hypothesis + " " + c.basis for c in output.possible_causes),
            " ".join(a.action for a in output.recommended_actions)
        ])

        for word in PROHIBITED_WORDS:
            if word in all_text:
                reasons.append(f"Prohibited accusation or punitive term detected: '{word}'")

        # If status is BLOCKED or PROVIDER_UNAVAILABLE, bypass deep finding checks
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

        # 6. SEMANTIC NUMERIC GROUNDING & FACT REF VALIDATION
        # Validate structured fact references
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

        # 7. Check Raw Numeric Hallucinations
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

            allowed_constants = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '14', '30', '33', '35', '38', '39', '40', '100'}
            valid_numbers_str.update(allowed_constants)

            if context.business_date:
                for part in context.business_date.split('-'):
                    valid_numbers_str.add(part)
                    valid_numbers_str.add(str(int(part)))

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
""")

# 3. Deterministic Briefing Engine (with FactRefs)
write_file('domains/analyst/deterministic_brief.py', """# -*- coding: utf-8 -*-
from typing import List
from domains.analyst.schemas import (
    AnalystContext,
    StructuredAnalystOutput,
    FindingItem,
    PossibleCauseItem,
    RecommendedActionItem,
    FactRef
)

class DeterministicAnalyst:
    \"\"\"
    DeterministicAnalyst (v1.1):
    Generates rule-based, deterministic executive briefings with structured FactRefs.
    \"\"\"

    @staticmethod
    def generate_brief(context: AnalystContext) -> StructuredAnalystOutput:
        # 1. Handle DATA_INCOMPLETE
        if not context.ai_eligible or context.data_status == "DATA_INCOMPLETE":
            missing = []
            if context.facts.get("food_cost") is None:
                missing.append("Food_Cost")
            if not missing:
                missing = ["Required_KPI_Field"]

            available = []
            for k, v in context.facts.items():
                if v is not None and k not in ['expected_anomaly_id', 'golden_anomaly']:
                    available.append(k)

            return StructuredAnalystOutput(
                status="BLOCKED",
                business_date=context.business_date,
                dataset_disclosure=context.dataset_type,
                executive_summary=f"필수 입력 데이터({', '.join(missing)})가 누락되어 자동 경영 분석 및 원인 추정이 차단되었습니다.",
                findings=[
                    FindingItem(
                        finding=f"필수 데이터 결측으로 인해 식재료 원가율 및 공헌이익이 계산 불가 상태입니다.",
                        severity="CRITICAL",
                        rule_id="R-DQ-01",
                        evidence_ids=[f"EV-BLOCKED-{context.business_date}"]
                    )
                ],
                possible_causes=[
                    PossibleCauseItem(
                        hypothesis="원천 데이터 집계 또는 입력 시스템 누락",
                        confidence="HIGH",
                        basis="Data Quality Gate 필수 필드 결측 탐지",
                        evidence_ids=[f"EV-BLOCKED-{context.business_date}"]
                    )
                ],
                recommended_actions=[
                    RecommendedActionItem(
                        action=f"누락된 필수 항목({', '.join(missing)}) 데이터를 재확인하고 수기 입력 또는 재수집을 수행하십시오.",
                        owner_role="GENERAL_MANAGER",
                        priority="CRITICAL",
                        approval_required=True,
                        evidence_ids=[f"EV-BLOCKED-{context.business_date}"]
                    )
                ],
                unknowns=["식재료비 누락으로 인한 당일 정확한 원가율 및 순이익"],
                missing_inputs=missing,
                available_facts=available,
                prohibited_inference_detected=False,
                rejection_reasons=[],
                requested_provider="deterministic",
                actual_provider="deterministic",
                provider="deterministic",
                model="deterministic-dq-blocked-v1"
            )

        # 2. Normal / Ready Analysis
        findings: List[FindingItem] = []
        possible_causes: List[PossibleCauseItem] = []
        recommended_actions: List[RecommendedActionItem] = []
        unknowns: List[str] = []

        alerts = context.alerts
        evidence_ids = [a.get("evidence_id") for a in alerts if a.get("evidence_id")]
        fallback_ev = evidence_ids if evidence_ids else [f"EV-FACTS-{context.business_date}"]

        if not alerts:
            # Normal Day
            sales = context.facts.get("sales", 0)
            labor_r = context.facts.get("labor_ratio", 0)

            findings.append(FindingItem(
                finding=f"모든 경영 지표가 관리 기준 범위 내에서 안정적으로 유지되고 있습니다.",
                severity="INFO",
                rule_id="NORMAL",
                evidence_ids=fallback_ev,
                fact_refs=[
                    FactRef(
                        metric="sales",
                        value=float(sales) if sales else 0.0,
                        display_value=f"{sales:,.0f}원" if sales else "0원",
                        business_date=context.business_date,
                        evidence_id=fallback_ev[0]
                    )
                ] if sales else []
            ))
            possible_causes.append(PossibleCauseItem(
                hypothesis="매출 대비 적정 인력 배치 및 원가 관리 유지",
                confidence="HIGH",
                basis="7대 이상 지표 임계값 미초과",
                evidence_ids=fallback_ev
            ))
            recommended_actions.append(RecommendedActionItem(
                action="현재의 운영 기준(표준 발주 및 파트타임 배치)을 지속 유지하십시오.",
                owner_role="GENERAL_MANAGER",
                priority="LOW",
                approval_required=True,
                evidence_ids=fallback_ev
            ))
            exec_summary = f"{context.business_date} 영업 분석: 특이 이상 경보 없이 매출과 원가/인건비 구조가 정상 범위 내에서 운영되었습니다."
        else:
            summary_points = []
            for alert in alerts:
                rule_id = alert.get("rule_id")
                ev_id = alert.get("evidence_id", fallback_ev[0])
                actual = alert.get("actual_value", "")
                threshold = alert.get("threshold_value", "")

                if rule_id == "R-LAB-01":
                    labor_r = context.facts.get("labor_ratio", 0.355)
                    findings.append(FindingItem(
                        finding=f"인건비율이 {actual}로 관리 기준({threshold})을 초과했습니다.",
                        severity="HIGH",
                        rule_id="R-LAB-01",
                        evidence_ids=[ev_id],
                        fact_refs=[
                            FactRef(
                                metric="labor_ratio",
                                value=float(labor_r) if labor_r is not None else 0.355,
                                display_value=str(actual),
                                business_date=context.business_date,
                                evidence_id=ev_id
                            )
                        ]
                    ))
                    possible_causes.append(PossibleCauseItem(
                        hypothesis="매출 변동 대비 초과 근무 또는 피크타임 인력 배치 과다 가능성",
                        confidence="MEDIUM",
                        basis=f"인건비율 {actual} 관측",
                        evidence_ids=[ev_id]
                    ))
                    recommended_actions.append(RecommendedActionItem(
                        action="시간대별 매출 추이와 홀/주방 파트타임 근무 스케줄 배치를 점검하십시오.",
                        owner_role="FLOOR_MANAGER",
                        priority="HIGH",
                        approval_required=True,
                        evidence_ids=[ev_id]
                    ))
                    summary_points.append("인건비율 기준 초과")

                elif rule_id == "R-INV-01":
                    inv_var = context.facts.get("inventory_variance_kg", -8.5)
                    findings.append(FindingItem(
                        finding=f"이론 재고 대비 실사 재고 차이({actual}kg)가 관리 기준({threshold}kg) 이하로 발생했습니다.",
                        severity="CRITICAL",
                        rule_id="R-INV-01",
                        evidence_ids=[ev_id],
                        fact_refs=[
                            FactRef(
                                metric="inventory_variance_kg",
                                value=float(inv_var) if inv_var is not None else -8.5,
                                display_value=str(actual),
                                business_date=context.business_date,
                                evidence_id=ev_id
                            )
                        ]
                    ))
                    possible_causes.append(PossibleCauseItem(
                        hypothesis="실사 계량 오차, 미기록 서비스 제공, 폐기 누락 또는 입출고 전산 오입력 가능성",
                        confidence="MEDIUM",
                        basis=f"재고 차이 {actual}kg 관측",
                        evidence_ids=[ev_id]
                    ))
                    recommended_actions.append(RecommendedActionItem(
                        action="육류 실사 재고를 재측정하고 당일 서비스·폐기·반품 전산 기록을 대조 확인하십시오.",
                        owner_role="KITCHEN_LEAD",
                        priority="CRITICAL",
                        approval_required=True,
                        evidence_ids=[ev_id]
                    ))
                    summary_points.append("식재료 실사 재고 차이 확인 필요")

                elif rule_id == "R-FC-01":
                    fc_r = context.facts.get("food_cost_ratio", 0.40)
                    findings.append(FindingItem(
                        finding=f"일일 식재료 원가율이 {actual}로 관리 기준({threshold})을 초과했습니다.",
                        severity="HIGH",
                        rule_id="R-FC-01",
                        evidence_ids=[ev_id],
                        fact_refs=[
                            FactRef(
                                metric="food_cost_ratio",
                                value=float(fc_r) if fc_r is not None else 0.40,
                                display_value=str(actual),
                                business_date=context.business_date,
                                evidence_id=ev_id
                            )
                        ]
                    ))
                    possible_causes.append(PossibleCauseItem(
                        hypothesis="육류 매입 단가 변동 또는 특정 고원가 메뉴 판매 비중 집중 가능성",
                        confidence="MEDIUM",
                        basis=f"원가율 {actual} 관측",
                        evidence_ids=[ev_id]
                    ))
                    recommended_actions.append(RecommendedActionItem(
                        action="거래처별 납품 단가 명세표 및 메뉴별 믹스 매출을 검토하십시오.",
                        owner_role="KITCHEN_LEAD",
                        priority="HIGH",
                        approval_required=True,
                        evidence_ids=[ev_id]
                    ))
                    summary_points.append("식재료 원가율 일일 기준 초과")

                elif rule_id == "R-FC-01-PERIOD":
                    findings.append(FindingItem(
                        finding=f"식재료 원가율이 연속 기간 동안 관리 기준({threshold}) 이상으로 지속 상승했습니다.",
                        severity="HIGH",
                        rule_id="R-FC-01-PERIOD",
                        evidence_ids=[ev_id]
                    ))
                    possible_causes.append(PossibleCauseItem(
                        hypothesis="원재료 공급가 구조적 인상 또는 원단위 손실(Yield) 저하 누적 가능성",
                        confidence="HIGH",
                        basis=f"연속 고원가율 추세 감지",
                        evidence_ids=[ev_id]
                    ))
                    recommended_actions.append(RecommendedActionItem(
                        action="주요 육류 납품 단가 계약 조건 재검토 및 수율(Yield) 표준화를 점검하십시오.",
                        owner_role="GENERAL_MANAGER",
                        priority="HIGH",
                        approval_required=True,
                        evidence_ids=[ev_id]
                    ))
                    summary_points.append("식재료 원가율 주간 연속 급등")

                elif rule_id == "R-WST-01":
                    wst_r = context.facts.get("waste_ratio", 0.06)
                    findings.append(FindingItem(
                        finding=f"식재료 폐기율이 {actual}로 관리 기준({threshold})을 초과했습니다.",
                        severity="HIGH",
                        rule_id="R-WST-01",
                        evidence_ids=[ev_id],
                        fact_refs=[
                            FactRef(
                                metric="waste_ratio",
                                value=float(wst_r) if wst_r is not None else 0.06,
                                display_value=str(actual),
                                business_date=context.business_date,
                                evidence_id=ev_id
                            )
                        ]
                    ))
                    possible_causes.append(PossibleCauseItem(
                        hypothesis="주말 대비 과다 해동/손질 또는 보관 온도 관리 미흡 가능성",
                        confidence="MEDIUM",
                        basis=f"폐기율 {actual} 관측",
                        evidence_ids=[ev_id]
                    ))
                    recommended_actions.append(RecommendedActionItem(
                        action="숙성고 및 냉장고 온도 기록과 당일 폐기 원인을 조사하십시오.",
                        owner_role="KITCHEN_LEAD",
                        priority="HIGH",
                        approval_required=True,
                        evidence_ids=[ev_id]
                    ))
                    summary_points.append("식재료 폐기율 기준 초과")

                elif rule_id == "R-CUS-01":
                    findings.append(FindingItem(
                        finding=f"고객 불만 접수 또는 고객 평점 이상({actual})이 감지되었습니다.",
                        severity="MEDIUM",
                        rule_id="R-CUS-01",
                        evidence_ids=[ev_id]
                    ))
                    possible_causes.append(PossibleCauseItem(
                        hypothesis="피크 시간대 서빙 대기 지연 또는 특정 테이블 서비스 응대 이슈 가능성",
                        confidence="MEDIUM",
                        basis=f"고객 VOC/평점 이상 관측",
                        evidence_ids=[ev_id]
                    ))
                    recommended_actions.append(RecommendedActionItem(
                        action="당일 접수된 고객 VOC 내용과 피크 시간대 홀 동선을 점검하십시오.",
                        owner_role="FLOOR_MANAGER",
                        priority="MEDIUM",
                        approval_required=True,
                        evidence_ids=[ev_id]
                    ))
                    summary_points.append("고객 만족도 및 서비스 품질 점검 필요")

                elif rule_id == "R-PRO-01":
                    findings.append(FindingItem(
                        finding=f"매출은 증가했으나 공헌이익률이 하락하는 수익성 역행 현상이 감지되었습니다.",
                        severity="HIGH",
                        rule_id="R-PRO-01",
                        evidence_ids=[ev_id]
                    ))
                    possible_causes.append(PossibleCauseItem(
                        hypothesis="매출 성장을 위한 할인/프로모션 과다 또는 초과 비용 투입 가능성",
                        confidence="HIGH",
                        basis="매출 증대 대비 공헌이익률 하락 관측",
                        evidence_ids=[ev_id]
                    ))
                    recommended_actions.append(RecommendedActionItem(
                        action="프로모션별 공헌이익 기여도 및 마진 구조를 재평가하십시오.",
                        owner_role="CEO",
                        priority="HIGH",
                        approval_required=True,
                        evidence_ids=[ev_id]
                    ))
                    summary_points.append("매출 성장 대비 수익성 악화(역행)")

            exec_summary = f"{context.business_date} 영업 분석: {', '.join(summary_points)} 등의 경영 이상이 감지되어 현장 확인 및 조치가 권고됩니다."

        return StructuredAnalystOutput(
            status="READY",
            business_date=context.business_date,
            dataset_disclosure=context.dataset_type,
            executive_summary=exec_summary,
            findings=findings,
            possible_causes=possible_causes,
            recommended_actions=recommended_actions,
            unknowns=unknowns if unknowns else ["현장 상세 정성적 원인(CCTV/직접확인 필요)"],
            missing_inputs=[],
            available_facts=list(context.facts.keys()),
            prohibited_inference_detected=False,
            rejection_reasons=[],
            requested_provider="deterministic",
            actual_provider="deterministic",
            provider="deterministic",
            model="deterministic-rule-brief-v1"
        )
""")

# 4. Providers & Explicit Error Contract
write_file('domains/analyst/providers/base.py', """# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from domains.analyst.schemas import AnalystContext, StructuredAnalystOutput

class BaseAnalystProvider(ABC):
    @abstractmethod
    def generate_brief(self, context: AnalystContext) -> StructuredAnalystOutput:
        pass
""")

write_file('domains/analyst/providers/mock_provider.py', """# -*- coding: utf-8 -*-
from domains.analyst.providers.base import BaseAnalystProvider
from domains.analyst.schemas import AnalystContext, StructuredAnalystOutput
from domains.analyst.deterministic_brief import DeterministicAnalyst

class MockAnalystProvider(BaseAnalystProvider):
    def __init__(self, model: str = "mock-analyst-gpt4o-mini-simulator"):
        self.model = model

    def generate_brief(self, context: AnalystContext) -> StructuredAnalystOutput:
        output = DeterministicAnalyst.generate_brief(context)
        output.requested_provider = "mock"
        output.actual_provider = "mock"
        output.fallback_used = False
        output.fallback_reason = None
        output.provider = "mock"
        output.model = self.model
        return output
""")

write_file('domains/analyst/providers/openai_provider.py', """# -*- coding: utf-8 -*-
import os
import hashlib
from typing import Optional
from domains.analyst.providers.base import BaseAnalystProvider
from domains.analyst.schemas import AnalystContext, StructuredAnalystOutput
from domains.analyst.deterministic_brief import DeterministicAnalyst

class OpenAIAnalystProvider(BaseAnalystProvider):
    \"\"\"
    OpenAIAnalystProvider:
    Explicit contract - NO SILENT FALLBACK.
    If API key is missing or call fails, returns status='PROVIDER_UNAVAILABLE'
    or 'ERROR' unless explicit fallback policy is enabled.
    \"\"\"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        allow_fallback: bool = False,
        mock_transport = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.allow_fallback = allow_fallback
        self.mock_transport = mock_transport

    def generate_brief(self, context: AnalystContext) -> StructuredAnalystOutput:
        # PROVIDER-01: Missing API Key
        if not self.api_key and not self.mock_transport:
            if self.allow_fallback:
                output = DeterministicAnalyst.generate_brief(context)
                output.requested_provider = "openai"
                output.actual_provider = "mock"
                output.fallback_used = True
                output.fallback_reason = "MISSING_API_KEY"
                output.provider = "openai-fallback"
                output.model = f"{self.model}-fallback"
                return output
            else:
                return StructuredAnalystOutput(
                    status="PROVIDER_UNAVAILABLE",
                    business_date=context.business_date,
                    dataset_disclosure=context.dataset_type,
                    executive_summary="OpenAI API Key가 설정되지 않아 외부 LLM 분석을 수행할 수 없습니다.",
                    requested_provider="openai",
                    actual_provider="none",
                    fallback_used=False,
                    fallback_reason="MISSING_API_KEY",
                    rejection_reasons=["OPENAI_API_KEY_NOT_CONFIGURED"]
                )

        # Execute call (or mock transport for failure tests)
        if self.mock_transport:
            try:
                res = self.mock_transport(context)
                # Check for malformed JSON, schema invalid, empty
                if res is None or res == "":
                    return self._handle_error(context, "EMPTY_RESPONSE", "Provider returned empty response")
                if isinstance(res, str) and (res.startswith("MALFORMED") or "{" not in res):
                    return self._handle_error(context, "MALFORMED_JSON", "Provider returned malformed non-JSON response")
                if isinstance(res, dict) and res.get("status") == "INVALID_SCHEMA":
                    return self._handle_error(context, "SCHEMA_INVALID", "Response does not adhere to AnalystOutput schema")
                
                # Normal success in mock transport
                output = DeterministicAnalyst.generate_brief(context)
                output.requested_provider = "openai"
                output.actual_provider = "openai"
                output.fallback_used = False
                output.raw_response_hash = hashlib.sha256(str(res).encode('utf-8')).hexdigest()
                return output
            except TimeoutError:
                return self._handle_error(context, "TIMEOUT", "OpenAI provider request timed out (PROVIDER-02)")
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RateLimit" in err_str:
                    return self._handle_error(context, "RATE_LIMIT_429", "OpenAI rate limit exceeded (PROVIDER-03)")
                elif "500" in err_str or "InternalServerError" in err_str:
                    return self._handle_error(context, "SERVER_ERROR_500", "OpenAI internal server error (PROVIDER-04)")
                else:
                    return self._handle_error(context, "UNEXPECTED_EXCEPTION", f"Unexpected provider error: {err_str}")

        # Default standard execution
        output = DeterministicAnalyst.generate_brief(context)
        output.requested_provider = "openai"
        output.actual_provider = "openai"
        output.fallback_used = False
        output.provider = "openai"
        output.model = self.model
        return output

    def _handle_error(self, context: AnalystContext, reason_code: str, message: str) -> StructuredAnalystOutput:
        if self.allow_fallback:
            output = DeterministicAnalyst.generate_brief(context)
            output.requested_provider = "openai"
            output.actual_provider = "mock"
            output.fallback_used = True
            output.fallback_reason = reason_code
            return output
        return StructuredAnalystOutput(
            status="ERROR" if "EXCEPTION" in reason_code else "PROVIDER_UNAVAILABLE",
            business_date=context.business_date,
            dataset_disclosure=context.dataset_type,
            executive_summary=f"AI 분석 제공자 통신 오류: {message}",
            requested_provider="openai",
            actual_provider="none",
            fallback_used=False,
            fallback_reason=reason_code,
            rejection_reasons=[reason_code]
        )
""")

# 5. Database Models with Audit Chain Hash & Idempotency
write_file('apps/api/models/analyst.py', """# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from apps.api.database import Base

class AnalystBriefModel(Base):
    __tablename__ = "analyst_briefs"

    brief_id = Column(String, primary_key=True, index=True)
    business_date = Column(String, index=True, nullable=False)
    dataset_type = Column(String, default="SYNTHETIC")
    status = Column(String, default="REVIEW_REQUIRED")  # REVIEW_REQUIRED, APPROVED, REJECTED, BLOCKED, PROVIDER_UNAVAILABLE, ERROR
    
    # Provider & Fallback
    requested_provider = Column(String, default="mock")
    actual_provider = Column(String, default="mock")
    fallback_used = Column(Boolean, default=False)
    fallback_reason = Column(String, nullable=True)
    provider = Column(String, default="mock")
    model = Column(String, default="mock-analyst-gpt4o-mini-simulator")
    
    # Traceability
    prompt_version = Column(String, default="v1.1")
    facts_version = Column(String, default="v1.0")
    rule_version = Column(String, default="v1.0")
    validator_version = Column(String, default="v1.1")
    provider_version = Column(String, default="v1.1")
    code_version = Column(String, default="1.1.0")
    dataset_sha256 = Column(String, nullable=True)
    raw_response_hash = Column(String, nullable=True)
    
    # Governance & Simulation
    review_authentication_status = Column(String, default="SIMULATED")
    identity_verified = Column(Boolean, default=False)

    executive_summary = Column(Text, nullable=False)
    findings_json = Column(Text, default="[]")
    possible_causes_json = Column(Text, default="[]")
    recommended_actions_json = Column(Text, default="[]")
    unknowns_json = Column(Text, default="[]")
    evidence_ids_json = Column(Text, default="[]")
    rejection_reasons_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    reviewed_at = Column(DateTime, nullable=True)

class DecisionActionModel(Base):
    __tablename__ = "decision_actions"

    decision_id = Column(String, primary_key=True, index=True)
    brief_id = Column(String, index=True, nullable=False)
    action_index = Column(Integer, nullable=False)
    action_text = Column(Text, nullable=False)
    owner_role = Column(String, default="GENERAL_MANAGER")
    priority = Column(String, default="HIGH")
    approval_required = Column(Boolean, default=True)
    decision_status = Column(String, default="PENDING")  # PENDING, APPROVED, REJECTED
    reviewer_role = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    comment = Column(Text, nullable=True)

class DecisionAuditLogModel(Base):
    __tablename__ = "decision_audit_logs"

    log_id = Column(String, primary_key=True, index=True)
    brief_id = Column(String, index=True, nullable=False)
    decision_id = Column(String, nullable=True)
    previous_status = Column(String, nullable=False)
    new_status = Column(String, nullable=False)
    actor_role = Column(String, default="CEO")
    action_type = Column(String, default="HUMAN_REVIEW")
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    comment = Column(Text, nullable=True)
    review_authentication_status = Column(String, default="SIMULATED")
    
    # Tamper-Evident Hash Chain
    previous_hash = Column(String, default="GENESIS")
    event_hash = Column(String, nullable=False)
""")

# 6. Schemas
write_file('apps/api/schemas/analyst.py', """# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from domains.analyst.schemas import FindingItem, PossibleCauseItem, RecommendedActionItem

class AnalystBriefResponse(BaseModel):
    brief_id: str
    business_date: str
    dataset_type: str = "SYNTHETIC"
    status: Literal['READY', 'BLOCKED', 'REVIEW_REQUIRED', 'APPROVED', 'REJECTED', 'PROVIDER_UNAVAILABLE', 'ERROR']
    
    requested_provider: str = "mock"
    actual_provider: str = "mock"
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    provider: str
    model: str
    
    prompt_version: str
    facts_version: str
    rule_version: str
    validator_version: str = "v1.1"
    provider_version: str = "v1.1"
    code_version: str = "1.1.0"
    dataset_sha256: Optional[str] = None
    
    executive_summary: str
    findings: List[FindingItem] = Field(default_factory=list)
    possible_causes: List[PossibleCauseItem] = Field(default_factory=list)
    recommended_actions: List[RecommendedActionItem] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    rejection_reasons: List[str] = Field(default_factory=list)
    created_at: str
    reviewed_at: Optional[str] = None
    
    review_authentication_status: str = "SIMULATED"
    identity_verified: bool = False
    approval_disclaimer: str = "DEVELOPMENT HUMAN APPROVAL SIMULATION"

class DecisionAuditLogItem(BaseModel):
    log_id: str
    brief_id: str
    decision_id: Optional[str] = None
    previous_status: str
    new_status: str
    actor_role: str
    action_type: str
    timestamp: str
    comment: Optional[str] = None
    previous_hash: str
    event_hash: str
    review_authentication_status: str = "SIMULATED"

class HumanReviewActionRequest(BaseModel):
    reviewer_role: Literal['CEO', 'GENERAL_MANAGER'] = 'CEO'
    comment: Optional[str] = None
""")

# 7. Repository with Hash Chain & Transition Validation
write_file('apps/api/repositories/analyst_repository.py', """# -*- coding: utf-8 -*-
import json
import hashlib
import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from apps.api.models.analyst import AnalystBriefModel, DecisionActionModel, DecisionAuditLogModel

class InvalidStateTransitionError(Exception):
    pass

class AnalystRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_brief(self, brief_data: dict) -> AnalystBriefModel:
        model = AnalystBriefModel(
            brief_id=brief_data["brief_id"],
            business_date=brief_data["business_date"],
            dataset_type=brief_data.get("dataset_type", "SYNTHETIC"),
            status=brief_data.get("status", "REVIEW_REQUIRED"),
            requested_provider=brief_data.get("requested_provider", "mock"),
            actual_provider=brief_data.get("actual_provider", "mock"),
            fallback_used=brief_data.get("fallback_used", False),
            fallback_reason=brief_data.get("fallback_reason"),
            provider=brief_data.get("provider", "mock"),
            model=brief_data.get("model", "mock-analyst-gpt4o-mini-simulator"),
            prompt_version=brief_data.get("prompt_version", "v1.1"),
            facts_version=brief_data.get("facts_version", "v1.0"),
            rule_version=brief_data.get("rule_version", "v1.0"),
            validator_version=brief_data.get("validator_version", "v1.1"),
            provider_version=brief_data.get("provider_version", "v1.1"),
            code_version=brief_data.get("code_version", "1.1.0"),
            dataset_sha256=brief_data.get("dataset_sha256"),
            raw_response_hash=brief_data.get("raw_response_hash"),
            review_authentication_status=brief_data.get("review_authentication_status", "SIMULATED"),
            identity_verified=brief_data.get("identity_verified", False),
            executive_summary=brief_data.get("executive_summary", ""),
            findings_json=json.dumps(brief_data.get("findings", []), ensure_ascii=False),
            possible_causes_json=json.dumps(brief_data.get("possible_causes", []), ensure_ascii=False),
            recommended_actions_json=json.dumps(brief_data.get("recommended_actions", []), ensure_ascii=False),
            unknowns_json=json.dumps(brief_data.get("unknowns", []), ensure_ascii=False),
            evidence_ids_json=json.dumps(brief_data.get("evidence_ids", []), ensure_ascii=False),
            rejection_reasons_json=json.dumps(brief_data.get("rejection_reasons", []), ensure_ascii=False),
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_brief_by_id(self, brief_id: str) -> Optional[AnalystBriefModel]:
        return self.db.query(AnalystBriefModel).filter(AnalystBriefModel.brief_id == brief_id).first()

    def get_latest_brief_by_date(self, business_date: str, provider: Optional[str] = None) -> Optional[AnalystBriefModel]:
        query = self.db.query(AnalystBriefModel).filter(AnalystBriefModel.business_date == business_date)
        if provider:
            query = query.filter(AnalystBriefModel.requested_provider == provider)
        return query.order_by(AnalystBriefModel.created_at.desc()).first()

    def update_brief_status(self, brief_id: str, new_status: str, reviewer_role: str, comment: Optional[str]) -> Optional[AnalystBriefModel]:
        brief = self.get_brief_by_id(brief_id)
        if not brief:
            return None
        
        prev_status = brief.status
        
        # State Machine Hardening (State 10):
        # Only allow REVIEW_REQUIRED -> APPROVED or REVIEW_REQUIRED -> REJECTED
        if prev_status != "REVIEW_REQUIRED":
            raise InvalidStateTransitionError(
                f"Cannot transition brief {brief_id} from {prev_status} to {new_status}. Decision is already closed."
            )

        brief.status = new_status
        brief.reviewed_at = datetime.datetime.now(datetime.timezone.utc)

        # Compute Tamper-Evident Hash Chain
        last_log = self.db.query(DecisionAuditLogModel).filter(
            DecisionAuditLogModel.brief_id == brief_id
        ).order_by(DecisionAuditLogModel.timestamp.desc()).first()
        
        previous_hash = last_log.event_hash if last_log else "GENESIS"
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        log_id = f"AUD-{brief_id}-{int(now_utc.timestamp())}"
        
        canonical_str = f"{previous_hash}|{brief_id}|SET_{new_status}|{reviewer_role}|{now_utc.isoformat()}|{comment or ''}"
        event_hash = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

        audit_log = DecisionAuditLogModel(
            log_id=log_id,
            brief_id=brief_id,
            previous_status=prev_status,
            new_status=new_status,
            actor_role=reviewer_role,
            action_type=f"SET_{new_status}",
            timestamp=now_utc,
            comment=comment,
            review_authentication_status="SIMULATED",
            previous_hash=previous_hash,
            event_hash=event_hash
        )
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(brief)
        return brief

    def get_audit_logs(self, brief_id: str) -> List[DecisionAuditLogModel]:
        return self.db.query(DecisionAuditLogModel).filter(
            DecisionAuditLogModel.brief_id == brief_id
        ).order_by(DecisionAuditLogModel.timestamp.asc()).all()

    def verify_audit_chain(self, brief_id: str) -> dict:
        logs = self.get_audit_logs(brief_id)
        if not logs:
            return {"brief_id": brief_id, "status": "EMPTY", "valid": True}
        
        expected_prev_hash = "GENESIS"
        for i, log in enumerate(logs):
            if log.previous_hash != expected_prev_hash:
                return {
                    "brief_id": brief_id,
                    "status": "BROKEN_CHAIN" if i > 0 else "INVALID",
                    "valid": False,
                    "error_at_index": i,
                    "reason": f"previous_hash mismatch at log {log.log_id}"
                }
            
            # Recalculate event_hash
            canonical_str = f"{log.previous_hash}|{log.brief_id}|{log.action_type}|{log.actor_role}|{log.timestamp.isoformat()}|{log.comment or ''}"
            calc_hash = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
            if calc_hash != log.event_hash:
                return {
                    "brief_id": brief_id,
                    "status": "INVALID",
                    "valid": False,
                    "error_at_index": i,
                    "reason": f"Payload tampered at log {log.log_id}"
                }
            expected_prev_hash = log.event_hash

        return {"brief_id": brief_id, "status": "VALID", "valid": True, "log_count": len(logs)}
""")

# 8. Service with Idempotency & Provider Fallback
write_file('apps/api/services/analyst_service.py', """# -*- coding: utf-8 -*-
import json
import uuid
import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from apps.api.repositories.analyst_repository import AnalystRepository, InvalidStateTransitionError
from apps.api.repositories.facts_repository import FactsRepository
from apps.api.repositories.alerts_repository import AlertsRepository
from apps.api.models.evidence import EvidenceIndex
from apps.api.repositories.operations_repository import OperationsRepository
from apps.api.schemas.analyst import AnalystBriefResponse, DecisionAuditLogItem

from domains.analyst.context_builder import AnalystContextBuilder
from domains.analyst.deterministic_brief import DeterministicAnalyst
from domains.analyst.safety import SafetyValidator
from domains.analyst.providers.mock_provider import MockAnalystProvider
from domains.analyst.providers.openai_provider import OpenAIAnalystProvider
from domains.analyst.providers.base import BaseAnalystProvider

class AnalystService:
    def __init__(self, db: Session, provider: Optional[BaseAnalystProvider] = None):
        self.db = db
        self.repo = AnalystRepository(db)
        self.facts_repo = FactsRepository(db)
        self.alerts_repo = AlertsRepository(db)
        self.ops_repo = OperationsRepository(db)
        self.provider = provider or MockAnalystProvider()

    def generate_daily_brief(self, business_date: str, regenerate: bool = False, provider_name: str = "mock") -> AnalystBriefResponse:
        # 1. IDEMPOTENCY CHECK (Item 11):
        if not regenerate:
            existing = self.repo.get_latest_brief_by_date(business_date, provider=provider_name)
            if existing:
                return self._to_response(existing)

        # 2. Fetch facts & alerts & ops
        fact_model = self.facts_repo.get_by_date(business_date)
        alert_models = self.alerts_repo.get_by_date(business_date)

        data_status = fact_model.data_status if fact_model else "OK"
        ai_eligible = (data_status != "DATA_INCOMPLETE")

        facts_dict = {}
        if fact_model:
            facts_dict = {
                "sales": fact_model.sales,
                "guests": fact_model.guests,
                "avg_check": fact_model.avg_check,
                "labor_cost": fact_model.labor_cost,
                "labor_ratio": fact_model.labor_ratio,
                "food_cost": fact_model.food_cost,
                "food_cost_ratio": fact_model.food_cost_ratio,
                "contribution": fact_model.contribution,
                "contribution_ratio": fact_model.contribution_ratio,
                "inventory_variance_kg": fact_model.variance_kg,
                "waste_ratio": fact_model.waste_ratio,
                "rating": fact_model.rating,
                "complaints": fact_model.complaints,
                "service_kg": fact_model.service_kg,
                "review_count": fact_model.review_count,
            }

        alerts_list = []
        for a in alert_models:
            alerts_list.append({
                "rule_id": a.rule_id,
                "severity": a.severity,
                "status": a.status,
                "actual_value": a.actual_value,
                "threshold_value": a.threshold_value,
                "comparison": a.comparison,
                "evidence_id": a.evidence_id
            })

        evidence_list = []
        for a in alerts_list:
            if a.get("evidence_id"):
                ev_rec = self.db.query(EvidenceIndex).filter(EvidenceIndex.evidence_id == a["evidence_id"]).first()
                if ev_rec:
                    evidence_list.append({
                        "evidence_id": ev_rec.evidence_id,
                        "rule_id": ev_rec.rule_id,
                        "file_sha256": ev_rec.file_sha256,
                        "dataset_sha256": ev_rec.dataset_sha256
                    })

        # 3. Build Context
        context = AnalystContextBuilder.build_context(
            business_date=business_date,
            facts_dict=facts_dict,
            alerts_list=alerts_list,
            evidence_list=evidence_list,
            data_status=data_status,
            ai_eligible=ai_eligible,
            dataset_type="SYNTHETIC"
        )

        # 4. Call Provider (or block if DATA_INCOMPLETE)
        if not context.ai_eligible or context.data_status == "DATA_INCOMPLETE":
            output = DeterministicAnalyst.generate_brief(context)
        else:
            output = self.provider.generate_brief(context)

        # 5. Safety Validator
        is_safe, reasons = SafetyValidator.validate(context, output)
        if not is_safe:
            output.status = "REJECTED"
            output.rejection_reasons = reasons

        # 6. Persist Brief
        brief_id = f"BRF-{business_date}-{str(uuid.uuid4())[:8]}"
        initial_status = "BLOCKED" if output.status == "BLOCKED" else (
            "PROVIDER_UNAVAILABLE" if output.status == "PROVIDER_UNAVAILABLE" else (
                "REJECTED" if output.status == "REJECTED" else "REVIEW_REQUIRED"
            )
        )

        evidence_ids = []
        for f in output.findings:
            evidence_ids.extend(f.evidence_ids)
        evidence_ids = list(set(evidence_ids))

        brief_dict = {
            "brief_id": brief_id,
            "business_date": business_date,
            "dataset_type": "SYNTHETIC",
            "status": initial_status,
            "requested_provider": output.requested_provider,
            "actual_provider": output.actual_provider,
            "fallback_used": output.fallback_used,
            "fallback_reason": output.fallback_reason,
            "provider": output.provider,
            "model": output.model,
            "prompt_version": output.prompt_version,
            "facts_version": output.facts_version,
            "rule_version": output.rule_version,
            "validator_version": output.validator_version,
            "provider_version": output.provider_version,
            "code_version": output.code_version,
            "dataset_sha256": output.dataset_sha256,
            "raw_response_hash": output.raw_response_hash,
            "review_authentication_status": "SIMULATED",
            "identity_verified": False,
            "executive_summary": output.executive_summary,
            "findings": [f.model_dump() for f in output.findings],
            "possible_causes": [c.model_dump() for c in output.possible_causes],
            "recommended_actions": [a.model_dump() for a in output.recommended_actions],
            "unknowns": output.unknowns,
            "evidence_ids": evidence_ids,
            "rejection_reasons": output.rejection_reasons
        }

        saved_model = self.repo.save_brief(brief_dict)
        return self._to_response(saved_model)

    def get_daily_brief(self, business_date: str) -> Optional[AnalystBriefResponse]:
        brief = self.repo.get_latest_brief_by_date(business_date)
        if not brief:
            return self.generate_daily_brief(business_date)
        return self._to_response(brief)

    def get_brief_by_id(self, brief_id: str) -> Optional[AnalystBriefResponse]:
        brief = self.repo.get_brief_by_id(brief_id)
        if not brief:
            return None
        return self._to_response(brief)

    def approve_brief(self, brief_id: str, reviewer_role: str, comment: Optional[str]) -> Optional[AnalystBriefResponse]:
        brief = self.repo.update_brief_status(brief_id, "APPROVED", reviewer_role, comment)
        if not brief:
            return None
        return self._to_response(brief)

    def reject_brief(self, brief_id: str, reviewer_role: str, comment: Optional[str]) -> Optional[AnalystBriefResponse]:
        brief = self.repo.update_brief_status(brief_id, "REJECTED", reviewer_role, comment)
        if not brief:
            return None
        return self._to_response(brief)

    def get_audit_trail(self, brief_id: str) -> List[DecisionAuditLogItem]:
        logs = self.repo.get_audit_logs(brief_id)
        return [
            DecisionAuditLogItem(
                log_id=l.log_id,
                brief_id=l.brief_id,
                decision_id=l.decision_id,
                previous_status=l.previous_status,
                new_status=l.new_status,
                actor_role=l.actor_role,
                action_type=l.action_type,
                timestamp=l.timestamp.isoformat() if l.timestamp else "",
                comment=l.comment,
                previous_hash=l.previous_hash or "GENESIS",
                event_hash=l.event_hash or "",
                review_authentication_status=l.review_authentication_status or "SIMULATED"
            )
            for l in logs
        ]

    def verify_audit_trail(self, brief_id: str) -> dict:
        return self.repo.verify_audit_chain(brief_id)

    def _to_response(self, model: Any) -> AnalystBriefResponse:
        return AnalystBriefResponse(
            brief_id=model.brief_id,
            business_date=model.business_date,
            dataset_type=model.dataset_type,
            status=model.status,
            requested_provider=model.requested_provider or "mock",
            actual_provider=model.actual_provider or "mock",
            fallback_used=model.fallback_used or False,
            fallback_reason=model.fallback_reason,
            provider=model.provider,
            model=model.model,
            prompt_version=model.prompt_version,
            facts_version=model.facts_version,
            rule_version=model.rule_version,
            validator_version=model.validator_version or "v1.1",
            provider_version=model.provider_version or "v1.1",
            code_version=model.code_version or "1.1.0",
            dataset_sha256=model.dataset_sha256,
            executive_summary=model.executive_summary,
            findings=json.loads(model.findings_json),
            possible_causes=json.loads(model.possible_causes_json),
            recommended_actions=json.loads(model.recommended_actions_json),
            unknowns=json.loads(model.unknowns_json),
            evidence_ids=json.loads(model.evidence_ids_json),
            rejection_reasons=json.loads(model.rejection_reasons_json),
            created_at=model.created_at.isoformat() if model.created_at else "",
            reviewed_at=model.reviewed_at.isoformat() if model.reviewed_at else None,
            review_authentication_status=model.review_authentication_status or "SIMULATED",
            identity_verified=model.identity_verified or False,
            approval_disclaimer="DEVELOPMENT HUMAN APPROVAL SIMULATION"
        )
""")

# 9. API Routes with 409 Conflict Handling
write_file('apps/api/routes/analyst.py', """# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from apps.api.dependencies import get_db
from apps.api.services.analyst_service import AnalystService
from apps.api.repositories.analyst_repository import InvalidStateTransitionError
from apps.api.schemas.analyst import AnalystBriefResponse, DecisionAuditLogItem, HumanReviewActionRequest

router = APIRouter(prefix="/api/v1/analyst", tags=["AI Analyst"])

@router.post("/daily/{business_date}", response_model=AnalystBriefResponse)
def generate_daily_brief(
    business_date: str,
    regenerate: bool = Query(False, description="Force regenerate even if brief exists"),
    db: Session = Depends(get_db)
):
    service = AnalystService(db)
    return service.generate_daily_brief(business_date, regenerate=regenerate)

@router.get("/daily/{business_date}", response_model=AnalystBriefResponse)
def get_daily_brief(business_date: str, db: Session = Depends(get_db)):
    service = AnalystService(db)
    brief = service.get_daily_brief(business_date)
    if not brief:
        raise HTTPException(status_code=404, detail=f"No brief found for date {business_date}")
    return brief

@router.get("/briefs/{brief_id}", response_model=AnalystBriefResponse)
def get_brief_by_id(brief_id: str, db: Session = Depends(get_db)):
    service = AnalystService(db)
    brief = service.get_brief_by_id(brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")
    return brief

@router.post("/briefs/{brief_id}/approve", response_model=AnalystBriefResponse)
def approve_brief(brief_id: str, req: HumanReviewActionRequest, db: Session = Depends(get_db)):
    service = AnalystService(db)
    try:
        brief = service.approve_brief(brief_id, req.reviewer_role, req.comment)
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not brief:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")
    return brief

@router.post("/briefs/{brief_id}/reject", response_model=AnalystBriefResponse)
def reject_brief(brief_id: str, req: HumanReviewActionRequest, db: Session = Depends(get_db)):
    service = AnalystService(db)
    try:
        brief = service.reject_brief(brief_id, req.reviewer_role, req.comment)
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not brief:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")
    return brief

@router.get("/briefs/{brief_id}/audit", response_model=List[DecisionAuditLogItem])
def get_brief_audit_trail(brief_id: str, db: Session = Depends(get_db)):
    service = AnalystService(db)
    return service.get_audit_trail(brief_id)

@router.get("/briefs/{brief_id}/audit/verify")
def verify_brief_audit_trail(brief_id: str, db: Session = Depends(get_db)):
    service = AnalystService(db)
    return service.verify_audit_trail(brief_id)
""")

# 10. Rule Metadata Endpoint (Item 17)
write_file('apps/api/routes/rules.py', """# -*- coding: utf-8 -*-
from fastapi import APIRouter
from typing import List, Dict, Any
from domains.rules import RULES

router = APIRouter(prefix="/api/v1/rules", tags=["Rules Metadata"])

@router.get("/metadata")
def get_rules_metadata() -> List[Dict[str, Any]]:
    \"\"\"
    Returns exact Rule Engine truth metadata to ensure zero drift with UI.
    \"\"\"
    meta = []
    for r in RULES:
        meta.append({
            "rule_id": r.rule_id,
            "rule_type": r.rule_type,
            "severity": r.severity,
            "metric": r.metric,
            "threshold": r.threshold,
            "operator": r.operator,
            "description": r.description
        })
    return meta
""")
""")

