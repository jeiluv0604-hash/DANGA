# -*- coding: utf-8 -*-
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
    dataset_type: Literal['SYNTHETIC', 'UNVERIFIED', 'PRODUCTION'] = 'SYNTHETIC'
    data_status: Literal['OK', 'DATA_INCOMPLETE'] = 'OK'
    ai_eligible: bool = True
    facts: Dict[str, Any] = Field(default_factory=dict)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    untrusted_text_data: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=lambda: {
        "no_new_numbers": True,
        "no_accusations": True,
        "human_approval_required": True,
        "synthetic_disclosure": True
    })

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

class HumanDecisionRequest(BaseModel):
    reviewer_role: Literal['CEO', 'GENERAL_MANAGER'] = 'CEO'
    comment: Optional[str] = None

class HumanDecisionResponse(BaseModel):
    brief_id: str
    status: Literal['APPROVED', 'REJECTED', 'REVIEW_REQUIRED']
    decision_id: str
    reviewer_role: str
    reviewed_at: str
    comment: Optional[str] = None
    review_authentication_status: str = "SIMULATED"

