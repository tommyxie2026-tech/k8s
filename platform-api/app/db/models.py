from __future__ import annotations

from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, ResourceMixin, utc_now
from app.utils.ids import new_resource_id


class WorkflowModel(ResourceMixin, Base):
    __tablename__ = "workflows"

    cluster_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    target_kind: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    destructive: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    phase: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    started_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(32), nullable=True)


class WorkflowStepPhase(StrEnum):
    pending = "pending"
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"
    cancelled = "cancelled"


class WorkflowStepModel(Base):
    __tablename__ = "workflow_steps"
    __table_args__ = (
        UniqueConstraint("workflow_id", "position", name="uq_workflow_steps_workflow_position"),
        UniqueConstraint("workflow_id", "name", name="uq_workflow_steps_workflow_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_resource_id)
    workflow_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    executor_type: Mapped[str] = mapped_column(String(32), nullable=False, default="ansible")
    command_ref: Mapped[str] = mapped_column(Text, nullable=False)
    input: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    depends_on: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    phase: Mapped[str] = mapped_column(
        String(32), nullable=False, default=WorkflowStepPhase.pending.value, index=True
    )
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    timeout_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now, index=True)
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, onupdate=utc_now
    )


class TaskPhase(StrEnum):
    pending = "pending"
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class TaskModel(ResourceMixin, Base):
    __tablename__ = "tasks"

    workflow_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    executor_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    command_ref: Mapped[str] = mapped_column(Text, nullable=False)
    phase: Mapped[str] = mapped_column(
        String(32), nullable=False, default=TaskPhase.pending.value, index=True
    )
    return_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    log_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(32), nullable=True)


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_resource_id)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    actor_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="system", index=True
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_kind: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    workflow_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    result: Mapped[str] = mapped_column(
        String(32), nullable=False, default="success", index=True
    )
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    source_ip: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, index=True
    )


class ResourceEventModel(Base):
    __tablename__ = "resource_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_resource_id)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    workflow_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    generation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resource_version: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, index=True
    )
