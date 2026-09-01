# -*- coding: utf-8 -*-
import datetime
import hashlib
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.dependencies import get_db
from apps.api.models.management import ManagementActionEventModel, ManagementActionModel
from apps.api.schemas.management import ActionTransitionRequest
from domains.management.prototype import (
    DATASET_TYPE,
    POLICY_STATUS,
    build_management_prototype,
    get_synthetic_actions,
    validate_action_transition,
)


router = APIRouter(prefix="/api/v1/management", tags=["Management System Prototype"])


def _seed_actions(db: Session) -> None:
    if db.query(ManagementActionModel).count() > 0:
        return
    for action in get_synthetic_actions():
        db.add(
            ManagementActionModel(
                **action,
                dataset_type=DATASET_TYPE,
                policy_status=POLICY_STATUS,
            )
        )
    db.commit()


def _action_dict(model: ManagementActionModel) -> Dict[str, Any]:
    return {
        "action_id": model.action_id,
        "title": model.title,
        "source_rule_id": model.source_rule_id,
        "sop_id": model.sop_id,
        "owner_role": model.owner_role,
        "priority": model.priority,
        "status": model.status,
        "due_date": model.due_date,
        "evidence_id": model.evidence_id,
        "dataset_type": model.dataset_type,
        "policy_status": model.policy_status,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


@router.get("/prototype")
def get_management_prototype(db: Session = Depends(get_db)) -> Dict[str, Any]:
    _seed_actions(db)
    payload = build_management_prototype()
    payload["standards"]["actions"] = [
        _action_dict(model)
        for model in db.query(ManagementActionModel).order_by(ManagementActionModel.action_id).all()
    ]
    return payload


@router.get("/finance")
def get_management_finance() -> Dict[str, Any]:
    payload = build_management_prototype()
    return {
        "brand_name": payload["brand_name"],
        "dataset_type": payload["dataset_type"],
        "policy_status": payload["policy_status"],
        **payload["finance"],
    }


@router.get("/menus")
def get_menu_engineering() -> Dict[str, Any]:
    payload = build_management_prototype()
    return {
        "brand_name": payload["brand_name"],
        "dataset_type": payload["dataset_type"],
        **payload["menu_engineering"],
    }


@router.get("/organization")
def get_organization() -> Dict[str, Any]:
    payload = build_management_prototype()
    return {
        "brand_name": payload["brand_name"],
        "dataset_type": payload["dataset_type"],
        "policy_status": payload["policy_status"],
        **payload["organization"],
    }


@router.get("/standards")
def get_standards() -> Dict[str, Any]:
    payload = build_management_prototype()
    return {
        "brand_name": payload["brand_name"],
        "dataset_type": payload["dataset_type"],
        **payload["standards"],
    }


@router.get("/actions")
def list_actions(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    _seed_actions(db)
    return [
        _action_dict(model)
        for model in db.query(ManagementActionModel).order_by(ManagementActionModel.action_id).all()
    ]


@router.post("/actions/{action_id}/transition")
def transition_action(
    action_id: str,
    request: ActionTransitionRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    _seed_actions(db)
    action = db.query(ManagementActionModel).filter(ManagementActionModel.action_id == action_id).first()
    if action is None:
        raise HTTPException(status_code=404, detail=f"Action {action_id} not found")
    if not validate_action_transition(action.status, request.new_status):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid action transition: {action.status} -> {request.new_status}",
        )
    latest_event = (
        db.query(ManagementActionEventModel)
        .filter(ManagementActionEventModel.action_id == action_id)
        .order_by(ManagementActionEventModel.id.desc())
        .first()
    )
    previous_hash = latest_event.event_hash if latest_event else "GENESIS"
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    event_id = f"AEV-{uuid.uuid4().hex[:12].upper()}"
    event_hash = hashlib.sha256(
        "|".join(
            [
                previous_hash,
                action_id,
                action.status,
                request.new_status,
                request.actor_role,
                timestamp.isoformat(),
                request.comment or "",
            ]
        ).encode("utf-8")
    ).hexdigest()
    event = ManagementActionEventModel(
        event_id=event_id,
        action_id=action_id,
        previous_status=action.status,
        new_status=request.new_status,
        actor_role=request.actor_role,
        comment=request.comment,
        previous_hash=previous_hash,
        event_hash=event_hash,
        dataset_type=DATASET_TYPE,
        created_at=timestamp,
    )
    action.status = request.new_status
    action.updated_at = timestamp
    db.add(event)
    db.commit()
    db.refresh(action)
    return {"action": _action_dict(action), "event_id": event_id, "event_hash": event_hash}


@router.get("/actions/{action_id}/audit")
def action_audit(action_id: str, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    events = (
        db.query(ManagementActionEventModel)
        .filter(ManagementActionEventModel.action_id == action_id)
        .order_by(ManagementActionEventModel.id)
        .all()
    )
    return [
        {
            "event_id": event.event_id,
            "action_id": event.action_id,
            "previous_status": event.previous_status,
            "new_status": event.new_status,
            "actor_role": event.actor_role,
            "comment": event.comment,
            "previous_hash": event.previous_hash,
            "event_hash": event.event_hash,
            "dataset_type": event.dataset_type,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]


@router.get("/reviews/monthly")
def get_monthly_review() -> Dict[str, Any]:
    payload = build_management_prototype()
    return {
        "brand_name": payload["brand_name"],
        "dataset_type": payload["dataset_type"],
        "policy_status": payload["policy_status"],
        **payload["monthly_review"],
    }

