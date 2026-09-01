# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from apps.api.database import Base

class AnalystBriefModel(Base):
    __tablename__ = "analyst_briefs"

    brief_id = Column(String, primary_key=True, index=True)
    business_date = Column(String, index=True, nullable=False)
    dataset_type = Column(String, default="SYNTHETIC")
    verification_status = Column(String, default="UNVERIFIED")
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
    timestamp = Column(String, default=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    comment = Column(Text, nullable=True)
    review_authentication_status = Column(String, default="SIMULATED")
    
    # Tamper-Evident Hash Chain
    previous_hash = Column(String, default="GENESIS")
    event_hash = Column(String, nullable=False)


