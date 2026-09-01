# -*- coding: utf-8 -*-
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
                timestamp=l.timestamp.isoformat() if hasattr(l.timestamp, 'isoformat') else str(l.timestamp or ''),
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

