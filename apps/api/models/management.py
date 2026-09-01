# -*- coding: utf-8 -*-
import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from apps.api.database import Base


class ManagementActionModel(Base):
    __tablename__ = "management_actions"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(Text, nullable=False)
    source_rule_id = Column(String(32), nullable=True)
    sop_id = Column(String(64), nullable=True)
    owner_role = Column(String(64), nullable=False)
    priority = Column(String(16), nullable=False)
    status = Column(String(32), nullable=False, default="OPEN")
    due_date = Column(String(10), nullable=True)
    evidence_id = Column(String(64), nullable=True)
    dataset_type = Column(String(32), nullable=False, default="SYNTHETIC")
    policy_status = Column(String(32), nullable=False, default="UNVERIFIED POLICY")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)


class ManagementActionEventModel(Base):
    __tablename__ = "management_action_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    action_id = Column(String(64), index=True, nullable=False)
    previous_status = Column(String(32), nullable=False)
    new_status = Column(String(32), nullable=False)
    actor_role = Column(String(64), nullable=False)
    comment = Column(Text, nullable=True)
    previous_hash = Column(String(64), nullable=False, default="GENESIS")
    event_hash = Column(String(64), nullable=False)
    dataset_type = Column(String(32), nullable=False, default="SYNTHETIC")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

