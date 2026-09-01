# -*- coding: utf-8 -*-
from typing import List
from domains.analyst.schemas import (
    AnalystContext,
    StructuredAnalystOutput,
    FindingItem,
    PossibleCauseItem,
    RecommendedActionItem
)

class DeterministicAnalyst:
    """
    DeterministicAnalyst:
    Generates rule-based, deterministic executive briefings for known alert patterns.
    Functions as the reliable Truth baseline and fallback before/alongside LLM providers.
    """

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
                        finding=f"필수 데이터 결측으로 인해 식재료 원가율 및 영업이익이 계산 불가 상태입니다.",
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
            guests = context.facts.get("guests", 0)
            labor_r = context.facts.get("labor_ratio", 0)
            fc_r = context.facts.get("food_cost_ratio", 0)

            findings.append(FindingItem(
                finding=f"모든 경영 지표가 관리 기준 범위 내에서 안정적으로 유지되고 있습니다.",
                severity="INFO",
                rule_id="NORMAL",
                evidence_ids=fallback_ev
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
            # Anomalies detected
            summary_points = []
            for alert in alerts:
                rule_id = alert.get("rule_id")
                ev_id = alert.get("evidence_id", fallback_ev[0])
                actual = alert.get("actual_value", "")
                threshold = alert.get("threshold_value", "")

                if rule_id == "R-LAB-01":
                    findings.append(FindingItem(
                        finding=f"인건비율이 {actual}로 관리 기준({threshold})을 초과했습니다.",
                        severity="HIGH",
                        rule_id="R-LAB-01",
                        evidence_ids=[ev_id]
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
                    findings.append(FindingItem(
                        finding=f"이론 재고 대비 실사 재고 차이({actual}kg)가 관리 기준({threshold}kg) 이하로 발생했습니다.",
                        severity="CRITICAL",
                        rule_id="R-INV-01",
                        evidence_ids=[ev_id]
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
                    findings.append(FindingItem(
                        finding=f"일일 식재료 원가율이 {actual}로 관리 기준({threshold})을 초과했습니다.",
                        severity="HIGH",
                        rule_id="R-FC-01",
                        evidence_ids=[ev_id]
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
                    findings.append(FindingItem(
                        finding=f"식재료 폐기율이 {actual}로 관리 기준({threshold})을 초과했습니다.",
                        severity="HIGH",
                        rule_id="R-WST-01",
                        evidence_ids=[ev_id]
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
                        finding=f"매출은 증가했으나 영업이익률이 하락하는 수익성 역행 현상이 감지되었습니다.",
                        severity="HIGH",
                        rule_id="R-PRO-01",
                        evidence_ids=[ev_id]
                    ))
                    possible_causes.append(PossibleCauseItem(
                        hypothesis="매출 성장을 위한 할인/프로모션 과다 또는 초과 비용 투입 가능성",
                        confidence="HIGH",
                        basis="매출 증대 대비 영업이익률 하락 관측",
                        evidence_ids=[ev_id]
                    ))
                    recommended_actions.append(RecommendedActionItem(
                        action="프로모션별 영업이익 기여도 및 마진 구조를 재평가하십시오.",
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
            provider="deterministic",
            model="deterministic-rule-brief-v1"
        )
