"""phase 6 management-system prototype

Revision ID: c6f9a1b2d3e4
Revises: ff4da1d3b951
Create Date: 2026-09-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c6f9a1b2d3e4"
down_revision: Union[str, Sequence[str], None] = "ff4da1d3b951"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    action_columns = {
        "id", "action_id", "title", "source_rule_id", "sop_id", "owner_role",
        "priority", "status", "due_date", "evidence_id", "dataset_type",
        "policy_status", "created_at", "updated_at",
    }
    event_columns = {
        "id", "event_id", "action_id", "previous_status", "new_status",
        "actor_role", "comment", "previous_hash", "event_hash", "dataset_type",
        "created_at",
    }

    if "management_actions" in existing_tables:
        actual = {column["name"] for column in inspector.get_columns("management_actions")}
        if actual != action_columns:
            raise RuntimeError("Existing management_actions schema does not match Phase 6 contract")
    else:
        op.create_table(
            "management_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("action_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("source_rule_id", sa.String(length=32), nullable=True),
        sa.Column("sop_id", sa.String(length=64), nullable=True),
        sa.Column("owner_role", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("due_date", sa.String(length=10), nullable=True),
        sa.Column("evidence_id", sa.String(length=64), nullable=True),
        sa.Column("dataset_type", sa.String(length=32), nullable=False),
        sa.Column("policy_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_management_actions_id", "management_actions", ["id"], unique=False)
        op.create_index("ix_management_actions_action_id", "management_actions", ["action_id"], unique=True)

    if "management_action_events" in existing_tables:
        actual = {column["name"] for column in inspector.get_columns("management_action_events")}
        if actual != event_columns:
            raise RuntimeError("Existing management_action_events schema does not match Phase 6 contract")
    else:
        op.create_table(
            "management_action_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("action_id", sa.String(length=64), nullable=False),
        sa.Column("previous_status", sa.String(length=32), nullable=False),
        sa.Column("new_status", sa.String(length=32), nullable=False),
        sa.Column("actor_role", sa.String(length=64), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("previous_hash", sa.String(length=64), nullable=False),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column("dataset_type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_management_action_events_id", "management_action_events", ["id"], unique=False)
        op.create_index("ix_management_action_events_event_id", "management_action_events", ["event_id"], unique=True)
        op.create_index("ix_management_action_events_action_id", "management_action_events", ["action_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_management_action_events_action_id", table_name="management_action_events")
    op.drop_index("ix_management_action_events_event_id", table_name="management_action_events")
    op.drop_index("ix_management_action_events_id", table_name="management_action_events")
    op.drop_table("management_action_events")
    op.drop_index("ix_management_actions_action_id", table_name="management_actions")
    op.drop_index("ix_management_actions_id", table_name="management_actions")
    op.drop_table("management_actions")
