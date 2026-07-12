from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.exceptions import ResourceNotFoundError, ResourceVersionConflictError
from app.db.models import WorkflowStepModel, WorkflowStepPhase


TERMINAL_STEP_PHASES = {
    WorkflowStepPhase.succeeded.value,
    WorkflowStepPhase.failed.value,
    WorkflowStepPhase.skipped.value,
    WorkflowStepPhase.cancelled.value,
}


class WorkflowStepRepository:
    """Persistence boundary for ordered workflow steps."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_many(
        self,
        workflow_id: str,
        steps: Iterable[dict[str, Any]],
    ) -> list[WorkflowStepModel]:
        records: list[WorkflowStepModel] = []
        for position, step in enumerate(steps):
            record = WorkflowStepModel(
                workflow_id=workflow_id,
                name=str(step["name"]),
                position=position,
                action=str(step.get("action") or step["name"]),
                executor_type=str(step.get("executor_type", "ansible")),
                command_ref=str(step["command_ref"]),
                input=dict(step.get("input") or {}),
                depends_on=list(step.get("depends_on") or []),
                phase=WorkflowStepPhase.pending.value,
                max_attempts=int(step.get("max_attempts", 1)),
                timeout_seconds=step.get("timeout_seconds"),
            )
            self.session.add(record)
            records.append(record)
        self.session.flush()
        return records

    def list_for_workflow(self, workflow_id: str) -> list[WorkflowStepModel]:
        statement = (
            select(WorkflowStepModel)
            .where(WorkflowStepModel.workflow_id == workflow_id)
            .order_by(WorkflowStepModel.position)
        )
        return list(self.session.scalars(statement))

    def get(self, step_id: str) -> WorkflowStepModel | None:
        return self.session.get(WorkflowStepModel, step_id)

    def require(self, step_id: str) -> WorkflowStepModel:
        step = self.get(step_id)
        if step is None:
            raise ResourceNotFoundError(f"workflow step not found: {step_id}")
        return step

    def set_phase(
        self,
        step_id: str,
        phase: str,
        *,
        task_id: str | None = None,
        error: str | None = None,
    ) -> WorkflowStepModel:
        step = self.require(step_id)
        if step.phase in TERMINAL_STEP_PHASES and step.phase != phase:
            raise ResourceVersionConflictError(
                f"terminal workflow step cannot transition from {step.phase} to {phase}"
            )

        step.phase = phase
        if task_id is not None:
            step.task_id = task_id
        if error is not None:
            step.error = error
        if phase == WorkflowStepPhase.running.value and step.started_at is None:
            step.started_at = utc_now()
            step.attempt += 1
        if phase in TERMINAL_STEP_PHASES:
            step.finished_at = utc_now()
        step.updated_at = utc_now()
        self.session.flush()
        return step
