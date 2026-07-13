"""Create CPP core persistence tables.

Revision ID: 0001_core_persistence
Revises:
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_core_persistence"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _resource_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("kind", sa.String(length=64), nullable=False),
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
        *_resource_columns(),
        sa.Column("cluster_id", sa.String(length=36), nullable=True),
        sa.Column("target_kind", sa.String(length=64), nullable=True),
        sa.Column("target_id", sa.String(length=36), nullable=True),
        sa.Column("destructive", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("phase", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.String(length=32), nullable=True),
        sa.Column("finished_at", sa.String(length=32), nullable=True),
    )
    op.create_index("ix_workflows_kind", "workflows", ["kind"])
    op.create_index("ix_workflows_cluster_id", "workflows", ["cluster_id"])
    op.create_index("ix_workflows_target_kind", "workflows", ["target_kind"])
    op.create_index("ix_workflows_target_id", "workflows", ["target_id"])
    op.create_index("ix_workflows_created_by", "workflows", ["created_by"])
    op.create_index("ix_workflows_phase", "workflows", ["phase"])

    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("workflow_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("executor_type", sa.String(length=32), nullable=False, server_default="ansible"),
        sa.Column("command_ref", sa.Text(), nullable=False),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("depends_on", sa.JSON(), nullable=False),
        sa.Column("phase", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("timeout_seconds", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.String(length=32), nullable=True),
        sa.Column("finished_at", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.UniqueConstraint("workflow_id", "position", name="uq_workflow_steps_workflow_position"),
        sa.UniqueConstraint("workflow_id", "name", name="uq_workflow_steps_workflow_name"),
    )
    op.create_index("ix_workflow_steps_workflow_id", "workflow_steps", ["workflow_id"])
    op.create_index("ix_workflow_steps_phase", "workflow_steps", ["phase"])
    op.create_index("ix_workflow_steps_task_id", "workflow_steps", ["task_id"])
    op.create_index("ix_workflow_steps_created_at", "workflow_steps", ["created_at"])

    op.create_table(
        "tasks",
        *_resource_columns(),
        sa.Column("workflow_id", sa.String(length=36), nullable=True),
        sa.Column("executor_type", sa.String(length=32), nullable=False),
        sa.Column("command_ref", sa.Text(), nullable=False),
        sa.Column("phase", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("return_code", sa.Integer(), nullable=True),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("log_path", sa.Text(), nullable=True),
        sa.Column("started_at", sa.String(length=32), nullable=True),
        sa.Column("finished_at", sa.String(length=32), nullable=True),
    )
    op.create_index("ix_tasks_kind", "tasks", ["kind"])
    op.create_index("ix_tasks_workflow_id", "tasks", ["workflow_id"])
    op.create_index("ix_tasks_executor_type", "tasks", ["executor_type"])
    op.create_index("ix_tasks_phase", "tasks", ["phase"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("actor_type", sa.String(length=32), nullable=False, server_default="system"),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("target_kind", sa.String(length=64), nullable=True),
        sa.Column("target_id", sa.String(length=36), nullable=True),
        sa.Column("workflow_id", sa.String(length=36), nullable=True),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("result", sa.String(length=32), nullable=False, server_default="success"),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("source_ip", sa.String(length=128), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
    )
    for column in (
        "actor_user_id",
        "actor_type",
        "action",
        "target_kind",
        "target_id",
        "workflow_id",
        "task_id",
        "result",
        "request_id",
        "created_at",
    ):
        op.create_index(f"ix_audit_events_{column}", "audit_events", [column])

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
    for column in (
        "event_type",
        "resource_kind",
        "resource_id",
        "actor_user_id",
        "workflow_id",
        "task_id",
        "created_at",
    ):
        op.create_index(f"ix_resource_events_{column}", "resource_events", [column])


def downgrade() -> None:
    op.drop_table("resource_events")
    op.drop_table("audit_events")
    op.drop_table("tasks")
    op.drop_table("workflow_steps")
    op.drop_table("workflows")
