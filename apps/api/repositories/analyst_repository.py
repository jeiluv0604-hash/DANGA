# -*- coding: utf-8 -*-
import json
import hashlib
import datetime
from typing import List, Optional
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
        ts_str = now_utc.isoformat()
        log_id = f"AUD-{brief_id}-{int(now_utc.timestamp())}"
        
        canonical_str = f"{previous_hash}|{brief_id}|SET_{new_status}|{reviewer_role}|{ts_str}|{comment or ''}"
        event_hash = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

        audit_log = DecisionAuditLogModel(
            log_id=log_id,
            brief_id=brief_id,
            previous_status=prev_status,
            new_status=new_status,
            actor_role=reviewer_role,
            action_type=f"SET_{new_status}",
            timestamp=ts_str,
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
        ).order_by(DecisionAuditLogModel.log_id.asc()).all()

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
            canonical_str = f"{log.previous_hash}|{log.brief_id}|{log.action_type}|{log.actor_role}|{str(log.timestamp)}|{log.comment or ''}"
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


