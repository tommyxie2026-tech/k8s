from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import WorkflowStepPhase
from app.db.repositories import (
    AuditEventRepository,
    ResourceEventRepository,
    TaskRepository,
    WorkflowRepository,
)
from app.db.workflow_steps import WorkflowStepRepository


@dataclass(frozen=True)
class WorkflowTimeoutResult:
    workflow_id: str
    step_id: str
    task_id: str | None
    timeout_seconds: int


class WorkflowTimeoutService:
    """Detect and persist expired workflow steps.

    Timeout is represented as a failed Step, failed Task (when attached), and
    failed Workflow. The service is idempotent because only running steps are
    selected and all terminal transitions are persisted in one transaction.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.steps = WorkflowStepRepository(session)
        self.workflows = WorkflowRepository(session)
        self.tasks = TaskRepository(session)
        self.audit_events = AuditEventRepository(session)
        self.resource_events = ResourceEventRepository(session)

    def expire_overdue(
        self,
        *,
        now: datetime | None = None,
    ) -> list[WorkflowTimeoutResult]:
        current = (now or datetime.now(UTC)).astimezone(UTC)
        results: list[WorkflowTimeoutResult] = []

        for step in self.steps.list_overdue_running(now=current):
            assert step.timeout_seconds is not None
            message = f"workflow step timed out after {step.timeout_seconds} seconds"

            if step.task_id is not None:
                self.tasks.fail(
                    step.task_id,
                    error=message,
                    return_code=124,
                )

            self.steps.set_phase(
                step.id,
                WorkflowStepPhase.failed,
                error=message,
            )
            workflow = self.workflows.require(step.workflow_id)
            if workflow.phase not in {"succeeded", "failed", "cancelled"}:
                workflow = self.workflows.set_phase(step.workflow_id, "failed")

            self.audit_events.append(
                action="workflow.step.timed_out",
                actor_type="system",
                target_kind="WorkflowStep",
                target_id=step.id,
                workflow_id=step.workflow_id,
                task_id=step.task_id,
                result="failed",
                details={
                    "step_name": step.name,
                    "timeout_seconds": step.timeout_seconds,
                },
            )
            self.resource_events.append(
                event_type="WorkflowStepTimedOut",
                resource_kind="Workflow",
                resource_id=step.workflow_id,
                workflow_id=step.workflow_id,
                task_id=step.task_id,
                resource_version=workflow.resource_version,
                payload={
                    "step_id": step.id,
                    "step_name": step.name,
                    "timeout_seconds": step.timeout_seconds,
                    "phase": workflow.phase,
                },
            )
            results.append(
                WorkflowTimeoutResult(
                    workflow_id=step.workflow_id,
                    step_id=step.id,
                    task_id=step.task_id,
                    timeout_seconds=step.timeout_seconds,
                )
            )

        self.session.commit()
        return results
