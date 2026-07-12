"""Create the CPP V2.0 persistence baseline.

Revision ID: 0001_persistence_baseline
Revises:
Create Date: 2026-07-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_persistence_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _resource_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
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
    op.create_index("ix_workflows_created_at", "workflows", ["created_at"])

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
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
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
    for name in (
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
        op.create_index(f"ix_audit_events_{name}", "audit_events", [name])

    op.create_table(
        "resource_events",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
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
    for name in (
        "event_type",
        "resource_kind",
        "resource_id",
        "actor_user_id",
        "workflow_id",
        "task_id",
        "created_at",
    ):
        op.create_index(f"ix_resource_events_{name}", "resource_events", [name])


def downgrade() -> None:
    op.drop_table("resource_events")
    op.drop_table("audit_events")
    op.drop_table("tasks")
    op.drop_table("workflows")
