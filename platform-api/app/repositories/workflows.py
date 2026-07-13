from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.models import WorkflowModel, WorkflowStepModel, WorkflowStepPhase


TERMINAL_WORKFLOW_PHASES = {"succeeded", "failed", "cancelled"}


class WorkflowNotFoundError(LookupError):
    pass


class InvalidWorkflowTransitionError(ValueError):
    pass


class WorkflowRepository:
    """Repository for Workflow resources and ordered WorkflowStep records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        name: str,
        steps: list[dict[str, Any]],
        cluster_id: str | None = None,
        target_kind: str | None = None,
        target_id: str | None = None,
        destructive: bool = False,
        created_by: str | None = None,
        spec: dict[str, Any] | None = None,
        status: dict[str, Any] | None = None,
    ) -> WorkflowModel:
        workflow = WorkflowModel(
            kind="Workflow",
            name=name,
            cluster_id=cluster_id,
            target_kind=target_kind,
            target_id=target_id,
            destructive=destructive,
            created_by=created_by,
            phase="pending",
            spec=spec or {},
            status=status or {"phase": "pending"},
        )
        self.session.add(workflow)
        self.session.flush()

        for position, item in enumerate(steps):
            step = WorkflowStepModel(
                workflow_id=workflow.id,
                name=str(item["name"]),
                position=position,
                action=str(item.get("action", item["name"])),
                executor_type=str(item.get("executor_type", "ansible")),
                command_ref=str(item["command_ref"]),
                input=dict(item.get("input", {})),
                depends_on=list(item.get("depends_on", [])),
                max_attempts=int(item.get("max_attempts", 1)),
                timeout_seconds=item.get("timeout_seconds"),
            )
            self.session.add(step)

        self.session.flush()
        return workflow

    def get(self, workflow_id: str, *, include_deleted: bool = False) -> WorkflowModel | None:
        stmt = select(WorkflowModel).where(WorkflowModel.id == workflow_id)
        if not include_deleted:
            stmt = stmt.where(WorkflowModel.deleted_at.is_(None))
        return self.session.scalar(stmt)

    def require(self, workflow_id: str, *, include_deleted: bool = False) -> WorkflowModel:
        workflow = self.get(workflow_id, include_deleted=include_deleted)
        if workflow is None:
            raise WorkflowNotFoundError(f"workflow not found: {workflow_id}")
        return workflow

    def list(
        self,
        *,
        cluster_id: str | None = None,
        phase: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[WorkflowModel]:
        stmt = (
            select(WorkflowModel)
            .order_by(WorkflowModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if cluster_id is not None:
            stmt = stmt.where(WorkflowModel.cluster_id == cluster_id)
        if phase is not None:
            stmt = stmt.where(WorkflowModel.phase == phase)
        if not include_deleted:
            stmt = stmt.where(WorkflowModel.deleted_at.is_(None))
        return self.session.scalars(stmt).all()

    def list_steps(self, workflow_id: str) -> Sequence[WorkflowStepModel]:
        self.require(workflow_id, include_deleted=True)
        stmt = (
            select(WorkflowStepModel)
            .where(WorkflowStepModel.workflow_id == workflow_id)
            .order_by(WorkflowStepModel.position.asc())
        )
        return self.session.scalars(stmt).all()

    def transition(self, workflow_id: str, phase: str) -> WorkflowModel:
        workflow = self.require(workflow_id)
        if workflow.phase in TERMINAL_WORKFLOW_PHASES and phase != workflow.phase:
            raise InvalidWorkflowTransitionError(
                f"terminal workflow {workflow_id} cannot transition from {workflow.phase} to {phase}"
            )

        workflow.phase = phase
        workflow.status = {**workflow.status, "phase": phase}
        if phase == "running" and workflow.started_at is None:
            workflow.started_at = utc_now()
        if phase in TERMINAL_WORKFLOW_PHASES:
            workflow.finished_at = workflow.finished_at or utc_now()
        workflow.touch_resource_version()
        self.session.flush()
        return workflow

    def transition_step(
        self,
        step_id: str,
        phase: WorkflowStepPhase | str,
        *,
        task_id: str | None = None,
        error: str | None = None,
    ) -> WorkflowStepModel:
        step = self.session.get(WorkflowStepModel, step_id)
        if step is None:
            raise LookupError(f"workflow step not found: {step_id}")

        next_phase = phase.value if isinstance(phase, WorkflowStepPhase) else phase
        step.phase = next_phase
        if next_phase == WorkflowStepPhase.running.value and step.started_at is None:
            step.started_at = utc_now()
        if next_phase in {
            WorkflowStepPhase.succeeded.value,
            WorkflowStepPhase.failed.value,
            WorkflowStepPhase.cancelled.value,
            WorkflowStepPhase.skipped.value,
        }:
            step.finished_at = step.finished_at or utc_now()
        if task_id is not None:
            step.task_id = task_id
        if error is not None:
            step.error = error
        step.updated_at = utc_now()
        self.session.flush()
        return step

    def replace_steps(self, workflow_id: str, steps: list[dict[str, Any]]) -> None:
        self.require(workflow_id)
        self.session.execute(
            delete(WorkflowStepModel).where(WorkflowStepModel.workflow_id == workflow_id)
        )
        for position, item in enumerate(steps):
            self.session.add(
                WorkflowStepModel(
                    workflow_id=workflow_id,
                    name=str(item["name"]),
                    position=position,
                    action=str(item.get("action", item["name"])),
                    executor_type=str(item.get("executor_type", "ansible")),
                    command_ref=str(item["command_ref"]),
                    input=dict(item.get("input", {})),
                    depends_on=list(item.get("depends_on", [])),
                    max_attempts=int(item.get("max_attempts", 1)),
                    timeout_seconds=item.get("timeout_seconds"),
                )
            )
        self.session.flush()

    def soft_delete(self, workflow_id: str) -> WorkflowModel:
        workflow = self.require(workflow_id)
        workflow.mark_deleted()
        self.session.flush()
        return workflow
