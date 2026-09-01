# -*- coding: utf-8 -*-
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

