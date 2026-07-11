"""create core execution tables

Revision ID: 0001_core_execution_tables
Revises:
Create Date: 2026-07-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_core_execution_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def resource_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("kind", sa.String(length=64), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("labels", sa.JSON(), nullable=False),
        sa.Column("annotations", sa.JSON(), nullable=False),
        sa.Column("spec", sa.JSON(), nullable=False),
        sa.Column("status", sa.JSON(), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("resource_version", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.Column("deleted_at", sa.String(length=32), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "workflows",
        *resource_columns(),
        sa.Column("cluster_id", sa.String(length=36), nullable=True),
        sa.Column("target_kind", sa.String(length=64), nullable=True),
        sa.Column("target_id", sa.String(length=36), nullable=True),
        sa.Column("destructive", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("phase", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.String(length=32), nullable=True),
        sa.Column("finished_at", sa.String(length=32), nullable=True),
    )
    op.create_index("idx_workflows_cluster", "workflows", ["cluster_id"])
    op.create_index("idx_workflows_phase", "workflows", ["phase"])
    op.create_index("idx_workflows_target", "workflows", ["target_kind", "target_id"])

    op.create_table(
        "tasks",
        *resource_columns(),
        sa.Column("workflow_id", sa.String(length=36), nullable=True),
        sa.Column("executor_type", sa.String(length=32), nullable=False),
        sa.Column("command_ref", sa.Text(), nullable=False),
        sa.Column("phase", sa.String(length=32), nullable=False),
        sa.Column("return_code", sa.Integer(), nullable=True),
        sa.Column("log_path", sa.Text(), nullable=True),
        sa.Column("started_at", sa.String(length=32), nullable=True),
        sa.Column("finished_at", sa.String(length=32), nullable=True),
    )
    op.create_index("idx_tasks_workflow", "tasks", ["workflow_id"])
    op.create_index("idx_tasks_executor_type", "tasks", ["executor_type"])
    op.create_index("idx_tasks_phase", "tasks", ["phase"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("target_kind", sa.String(length=64), nullable=True),
        sa.Column("target_id", sa.String(length=36), nullable=True),
        sa.Column("workflow_id", sa.String(length=36), nullable=True),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("source_ip", sa.String(length=128), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
    )
    op.create_index("idx_audit_events_actor", "audit_events", ["actor_user_id"])
    op.create_index("idx_audit_events_action", "audit_events", ["action"])
    op.create_index("idx_audit_events_target", "audit_events", ["target_kind", "target_id"])
    op.create_index("idx_audit_events_created_at", "audit_events", ["created_at"])

    op.create_table(
        "resource_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("resource_kind", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=36), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("workflow_id", sa.String(length=36), nullable=True),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("generation", sa.Integer(), nullable=True),
        sa.Column("resource_version", sa.String(length=36), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
    )
    op.create_index("idx_resource_events_type", "resource_events", ["event_type"])
    op.create_index("idx_resource_events_resource", "resource_events", ["resource_kind", "resource_id"])
    op.create_index("idx_resource_events_created_at", "resource_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("resource_events")
    op.drop_table("audit_events")
    op.drop_table("tasks")
    op.drop_table("workflows")
