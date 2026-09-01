# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print('Wrote:', path)

# 1. Models
write_file('apps/api/models/analyst.py', """# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from apps.api.database import Base

class AnalystBriefModel(Base):
    __tablename__ = "analyst_briefs"

    brief_id = Column(String, primary_key=True, index=True)
    business_date = Column(String, index=True, nullable=False)
    dataset_type = Column(String, default="SYNTHETIC")
    status = Column(String, default="REVIEW_REQUIRED")  # REVIEW_REQUIRED, APPROVED, REJECTED, BLOCKED
    provider = Column(String, default="mock")
    model = Column(String, default="mock-analyst-gpt4o-mini-simulator")
    prompt_version = Column(String, default="v1.0")
    facts_version = Column(String, default="v1.0")
    rule_version = Column(String, default="v1.0")
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
""")

# 2. Schemas
write_file('apps/api/schemas/analyst.py', """# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from domains.analyst.schemas import FindingItem, PossibleCauseItem, RecommendedActionItem

class AnalystBriefResponse(BaseModel):
    brief_id: str
    business_date: str
    dataset_type: str = "SYNTHETIC"
    status: Literal['READY', 'BLOCKED', 'REVIEW_REQUIRED', 'APPROVED', 'REJECTED']
    provider: str
    model: str
    prompt_version: str
    facts_version: str
    rule_version: str
    executive_summary: str
    findings: List[FindingItem] = Field(default_factory=list)
    possible_causes: List[PossibleCauseItem] = Field(default_factory=list)
    recommended_actions: List[RecommendedActionItem] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    rejection_reasons: List[str] = Field(default_factory=list)
    created_at: str
    reviewed_at: Optional[str] = None
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

class HumanReviewActionRequest(BaseModel):
    reviewer_role: Literal['CEO', 'GENERAL_MANAGER'] = 'CEO'
    comment: Optional[str] = None
""")

# 3. Repository
write_file('apps/api/repositories/analyst_repository.py', """# -*- coding: utf-8 -*-
import json
import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from apps.api.models.analyst import AnalystBriefModel, DecisionActionModel, DecisionAuditLogModel

class AnalystRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_brief(self, brief_data: dict) -> AnalystBriefModel:
        model = AnalystBriefModel(
            brief_id=brief_data["brief_id"],
            business_date=brief_data["business_date"],
            dataset_type=brief_data.get("dataset_type", "SYNTHETIC"),
            status=brief_data.get("status", "REVIEW_REQUIRED"),
            provider=brief_data.get("provider", "mock"),
            model=brief_data.get("model", "mock-analyst-gpt4o-mini-simulator"),
            prompt_version=brief_data.get("prompt_version", "v1.0"),
            facts_version=brief_data.get("facts_version", "v1.0"),
            rule_version=brief_data.get("rule_version", "v1.0"),
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

    def get_latest_brief_by_date(self, business_date: str) -> Optional[AnalystBriefModel]:
        return self.db.query(AnalystBriefModel).filter(
            AnalystBriefModel.business_date == business_date
        ).order_by(AnalystBriefModel.created_at.desc()).first()

    def update_brief_status(self, brief_id: str, new_status: str, reviewer_role: str, comment: Optional[str]) -> Optional[AnalystBriefModel]:
        brief = self.get_brief_by_id(brief_id)
        if not brief:
            return None
        
        prev_status = brief.status
        brief.status = new_status
        brief.reviewed_at = datetime.datetime.now(datetime.timezone.utc)

        # Create audit log
        log_id = f"AUD-{brief_id}-{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
        audit_log = DecisionAuditLogModel(
            log_id=log_id,
            brief_id=brief_id,
            previous_status=prev_status,
            new_status=new_status,
            actor_role=reviewer_role,
            action_type=f"SET_{new_status}",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            comment=comment
        )
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(brief)
        return brief

    def get_audit_logs(self, brief_id: str) -> List[DecisionAuditLogModel]:
        return self.db.query(DecisionAuditLogModel).filter(
            DecisionAuditLogModel.brief_id == brief_id
        ).order_by(DecisionAuditLogModel.timestamp.asc()).all()
""")

# 4. Service
write_file('apps/api/services/analyst_service.py', """# -*- coding: utf-8 -*-
import json
import uuid
import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from apps.api.repositories.analyst_repository import AnalystRepository
from apps.api.repositories.facts_repository import FactsRepository
from apps.api.repositories.alerts_repository import AlertsRepository
from apps.api.repositories.evidence_repository import EvidenceRepository
from apps.api.repositories.operations_repository import OperationsRepository
from apps.api.schemas.analyst import AnalystBriefResponse, DecisionAuditLogItem

from domains.analyst.context_builder import AnalystContextBuilder
from domains.analyst.deterministic_brief import DeterministicAnalyst
from domains.analyst.safety import SafetyValidator
from domains.analyst.providers.mock_provider import MockAnalystProvider
from domains.analyst.providers.base import BaseAnalystProvider

class AnalystService:
    def __init__(self, db: Session, provider: Optional[BaseAnalystProvider] = None):
        self.db = db
        self.repo = AnalystRepository(db)
        self.facts_repo = FactsRepository(db)
        self.alerts_repo = AlertsRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.ops_repo = OperationsRepository(db)
        self.provider = provider or MockAnalystProvider()

    def generate_daily_brief(self, business_date: str) -> AnalystBriefResponse:
        # 1. Fetch facts & alerts & ops
        fact_model = self.facts_repo.get_by_date(business_date)
        alert_models = self.alerts_repo.get_by_date(business_date)
        op_model = self.ops_repo.get_by_date(business_date)

        data_status = op_model.data_status if op_model else "OK"
        ai_eligible = op_model.ai_eligible if op_model else True

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
                "inventory_variance_kg": fact_model.inventory_variance_kg,
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
                ev_rec = self.evidence_repo.get_by_id(a["evidence_id"])
                if ev_rec:
                    evidence_list.append({
                        "evidence_id": ev_rec.evidence_id,
                        "rule_id": ev_rec.rule_id,
                        "file_sha256": ev_rec.file_sha256,
                        "dataset_sha256": ev_rec.dataset_sha256
                    })

        # 2. Build Context
        context = AnalystContextBuilder.build_context(
            business_date=business_date,
            facts_dict=facts_dict,
            alerts_list=alerts_list,
            evidence_list=evidence_list,
            data_status=data_status,
            ai_eligible=ai_eligible,
            dataset_type="SYNTHETIC"
        )

        # 3. Call Provider (or block if DATA_INCOMPLETE)
        if not context.ai_eligible or context.data_status == "DATA_INCOMPLETE":
            output = DeterministicAnalyst.generate_brief(context)
        else:
            output = self.provider.generate_brief(context)

        # 4. Safety Validator
        is_safe, reasons = SafetyValidator.validate(context, output)
        if not is_safe:
            output.status = "REJECTED"
            output.rejection_reasons = reasons

        # 5. Persist Brief
        brief_id = f"BRF-{business_date}-{str(uuid.uuid4())[:8]}"
        initial_status = "BLOCKED" if output.status == "BLOCKED" else ("REJECTED" if output.status == "REJECTED" else "REVIEW_REQUIRED")

        evidence_ids = []
        for f in output.findings:
            evidence_ids.extend(f.evidence_ids)
        evidence_ids = list(set(evidence_ids))

        brief_dict = {
            "brief_id": brief_id,
            "business_date": business_date,
            "dataset_type": "SYNTHETIC",
            "status": initial_status,
            "provider": output.provider,
            "model": output.model,
            "prompt_version": output.prompt_version,
            "facts_version": output.facts_version,
            "rule_version": output.rule_version,
            "executive_summary": output.executive_summary,
            "findings": [f.dict() for f in output.findings],
            "possible_causes": [c.dict() for c in output.possible_causes],
            "recommended_actions": [a.dict() for a in output.recommended_actions],
            "unknowns": output.unknowns,
            "evidence_ids": evidence_ids,
            "rejection_reasons": output.rejection_reasons
        }

        saved_model = self.repo.save_brief(brief_dict)
        return self._to_response(saved_model)

    def get_daily_brief(self, business_date: str) -> Optional[AnalystBriefResponse]:
        brief = self.repo.get_latest_brief_by_date(business_date)
        if not brief:
            # If not yet generated, auto-generate and return
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
                comment=l.comment
            )
            for l in logs
        ]

    def _to_response(self, model: Any) -> AnalystBriefResponse:
        return AnalystBriefResponse(
            brief_id=model.brief_id,
            business_date=model.business_date,
            dataset_type=model.dataset_type,
            status=model.status,
            provider=model.provider,
            model=model.model,
            prompt_version=model.prompt_version,
            facts_version=model.facts_version,
            rule_version=model.rule_version,
            executive_summary=model.executive_summary,
            findings=json.loads(model.findings_json),
            possible_causes=json.loads(model.possible_causes_json),
            recommended_actions=json.loads(model.recommended_actions_json),
            unknowns=json.loads(model.unknowns_json),
            evidence_ids=json.loads(model.evidence_ids_json),
            rejection_reasons=json.loads(model.rejection_reasons_json),
            created_at=model.created_at.isoformat() if model.created_at else "",
            reviewed_at=model.reviewed_at.isoformat() if model.reviewed_at else None,
            approval_disclaimer="DEVELOPMENT HUMAN APPROVAL SIMULATION"
        )
""")

# 5. Routes
write_file('apps/api/routes/analyst.py', """# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.dependencies import get_db
from apps.api.services.analyst_service import AnalystService
from apps.api.schemas.analyst import AnalystBriefResponse, DecisionAuditLogItem, HumanReviewActionRequest

router = APIRouter(prefix="/analyst", tags=["AI Analyst"])

@router.post("/daily/{business_date}", response_model=AnalystBriefResponse)
def generate_daily_brief(business_date: str, db: Session = Depends(get_db)):
    service = AnalystService(db)
    return service.generate_daily_brief(business_date)

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
    brief = service.approve_brief(brief_id, req.reviewer_role, req.comment)
    if not brief:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")
    return brief

@router.post("/briefs/{brief_id}/reject", response_model=AnalystBriefResponse)
def reject_brief(brief_id: str, req: HumanReviewActionRequest, db: Session = Depends(get_db)):
    service = AnalystService(db)
    brief = service.reject_brief(brief_id, req.reviewer_role, req.comment)
    if not brief:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")
    return brief

@router.get("/briefs/{brief_id}/audit", response_model=List[DecisionAuditLogItem])
def get_brief_audit_trail(brief_id: str, db: Session = Depends(get_db)):
    service = AnalystService(db)
    return service.get_audit_trail(brief_id)
""")


