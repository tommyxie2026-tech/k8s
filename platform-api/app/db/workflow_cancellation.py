from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.exceptions import ResourceNotFoundError, ResourceVersionConflictError
from app.db.models import TaskModel, WorkflowModel, WorkflowStepModel


@dataclass(frozen=True)
class WorkflowCancellationResult:
    workflow_id: str
    workflow_phase: str
    cancelled_task_ids: tuple[str, ...]
    cancellation_requested_task_ids: tuple[str, ...]
    cancelled_step_ids: tuple[str, ...]
    cancellation_requested_step_ids: tuple[str, ...]


class WorkflowCancellationRepository:
    """Persist a safe two-phase workflow cancellation request.

    Pending and queued work can be cancelled immediately. Running work is only
    marked with ``cancellation_requested`` so the Runtime Plane can stop the
    underlying process before reporting a terminal cancelled state.
    """

    TERMINAL_PHASES = {"succeeded", "failed", "cancelled"}
    IMMEDIATELY_CANCELLABLE_PHASES = {"pending", "queued"}

    def __init__(self, session: Session) -> None:
        self.session = session

    def request_cancel(self, workflow_id: str, *, reason: str | None = None) -> WorkflowCancellationResult:
        workflow = self.session.get(WorkflowModel, workflow_id)
        if workflow is None or workflow.deleted_at is not None:
            raise ResourceNotFoundError(f"workflow not found: {workflow_id}")
        if workflow.phase in self.TERMINAL_PHASES:
            raise ResourceVersionConflictError(
                f"terminal workflow cannot be cancelled: {workflow.phase}"
            )

        cancelled_task_ids: list[str] = []
        requested_task_ids: list[str] = []
        cancelled_step_ids: list[str] = []
        requested_step_ids: list[str] = []
        now = utc_now()

        tasks = self.session.scalars(
            select(TaskModel).where(
                TaskModel.workflow_id == workflow_id,
                TaskModel.deleted_at.is_(None),
            )
        ).all()
        for task in tasks:
            if task.phase in self.IMMEDIATELY_CANCELLABLE_PHASES:
                task.phase = "cancelled"
                task.finished_at = now
                task.status = {
                    **task.status,
                    "phase": "cancelled",
                    "cancellation_requested": True,
                    "cancellation_reason": reason,
                }
                task.touch_resource_version()
                cancelled_task_ids.append(task.id)
            elif task.phase == "running":
                task.status = {
                    **task.status,
                    "cancellation_requested": True,
                    "cancellation_reason": reason,
                }
                task.touch_resource_version()
                requested_task_ids.append(task.id)

        steps = self.session.scalars(
            select(WorkflowStepModel).where(WorkflowStepModel.workflow_id == workflow_id)
        ).all()
        for step in steps:
            if step.phase in self.IMMEDIATELY_CANCELLABLE_PHASES:
                step.phase = "cancelled"
                step.finished_at = now
                step.error = reason
                cancelled_step_ids.append(step.id)
            elif step.phase == "running":
                step.input = {
                    **step.input,
                    "cancellation_requested": True,
                    "cancellation_reason": reason,
                }
                requested_step_ids.append(step.id)

        cancellation_pending = bool(requested_task_ids or requested_step_ids)
        workflow.status = {
            **workflow.status,
            "cancellation_requested": True,
            "cancellation_reason": reason,
            "cancellation_pending": cancellation_pending,
        }
        if cancellation_pending:
            workflow.phase = "running"
            workflow.status = {**workflow.status, "phase": "running"}
        else:
            workflow.phase = "cancelled"
            workflow.finished_at = now
            workflow.status = {**workflow.status, "phase": "cancelled"}
        workflow.touch_resource_version()

        self.session.flush()
        return WorkflowCancellationResult(
            workflow_id=workflow.id,
            workflow_phase=workflow.phase,
            cancelled_task_ids=tuple(cancelled_task_ids),
            cancellation_requested_task_ids=tuple(requested_task_ids),
            cancelled_step_ids=tuple(cancelled_step_ids),
            cancellation_requested_step_ids=tuple(requested_step_ids),
        )

    def finalize_cancel(self, workflow_id: str) -> WorkflowModel:
        """Mark a cancellation-requested workflow terminal after Runtime stops work."""
        workflow = self.session.get(WorkflowModel, workflow_id)
        if workflow is None or workflow.deleted_at is not None:
            raise ResourceNotFoundError(f"workflow not found: {workflow_id}")
        if not workflow.status.get("cancellation_requested"):
            raise ResourceVersionConflictError(
                f"workflow has no cancellation request: {workflow_id}"
            )

        running_tasks = self.session.scalars(
            select(TaskModel).where(
                TaskModel.workflow_id == workflow_id,
                TaskModel.phase == "running",
                TaskModel.deleted_at.is_(None),
            )
        ).first()
        running_steps = self.session.scalars(
            select(WorkflowStepModel).where(
                WorkflowStepModel.workflow_id == workflow_id,
                WorkflowStepModel.phase == "running",
            )
        ).first()
        if running_tasks is not None or running_steps is not None:
            raise ResourceVersionConflictError(
                f"workflow still has running work: {workflow_id}"
            )

        now = utc_now()
        workflow.phase = "cancelled"
        workflow.finished_at = now
        workflow.status = {
            **workflow.status,
            "phase": "cancelled",
            "cancellation_pending": False,
        }
        workflow.touch_resource_version()
        self.session.flush()
        return workflow
