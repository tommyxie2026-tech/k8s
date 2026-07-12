from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.exceptions import ResourceNotFoundError
from app.db.models import WorkflowStepModel, WorkflowStepPhase
from app.services.workflow_state import transition_step


TERMINAL_STEP_PHASES = {
    WorkflowStepPhase.succeeded.value,
    WorkflowStepPhase.failed.value,
    WorkflowStepPhase.skipped.value,
    WorkflowStepPhase.cancelled.value,
}


class WorkflowStepRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        workflow_id: str,
        name: str,
        position: int,
        action: str,
        command_ref: str,
        executor_type: str = "ansible",
        input: dict | None = None,
        depends_on: list[str] | None = None,
        max_attempts: int = 1,
        timeout_seconds: int | None = None,
    ) -> WorkflowStepModel:
        if position < 0:
            raise ValueError("workflow step position must be non-negative")
        if max_attempts < 1:
            raise ValueError("workflow step max_attempts must be at least 1")

        step = WorkflowStepModel(
            workflow_id=workflow_id,
            name=name,
            position=position,
            action=action,
            executor_type=executor_type,
            command_ref=command_ref,
            input=input or {},
            depends_on=depends_on or [],
            max_attempts=max_attempts,
            timeout_seconds=timeout_seconds,
            phase=WorkflowStepPhase.pending.value,
        )
        self.session.add(step)
        self.session.flush()
        return step

    def get(self, step_id: str) -> WorkflowStepModel | None:
        return self.session.get(WorkflowStepModel, step_id)

    def require(self, step_id: str) -> WorkflowStepModel:
        step = self.get(step_id)
        if step is None:
            raise ResourceNotFoundError(f"workflow step not found: {step_id}")
        return step

    def list_for_workflow(self, workflow_id: str) -> list[WorkflowStepModel]:
        statement = (
            select(WorkflowStepModel)
            .where(WorkflowStepModel.workflow_id == workflow_id)
            .order_by(WorkflowStepModel.position, WorkflowStepModel.id)
        )
        return list(self.session.scalars(statement))

    def set_phase(
        self,
        step_id: str,
        phase: WorkflowStepPhase | str,
        *,
        task_id: str | None = None,
        error: str | None = None,
    ) -> WorkflowStepModel:
        step = self.require(step_id)
        requested = phase.value if isinstance(phase, WorkflowStepPhase) else phase
        next_phase = transition_step(step.phase, requested)

        now = utc_now()
        step.phase = next_phase.value
        step.updated_at = now
        if task_id is not None:
            step.task_id = task_id
        if error is not None:
            step.error = error
        if next_phase is WorkflowStepPhase.running:
            step.started_at = step.started_at or now
            step.attempt += 1
        if next_phase.value in TERMINAL_STEP_PHASES:
            step.finished_at = now

        self.session.flush()
        return step
