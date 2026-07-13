from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.repositories import AuditEventRepository, ResourceEventRepository, WorkflowRepository
from app.db.workflow_steps import WorkflowStepRepository


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded exponential retry policy for workflow steps."""

    initial_backoff_seconds: int = 5
    multiplier: float = 2.0
    max_backoff_seconds: int = 300

    def __post_init__(self) -> None:
        if self.initial_backoff_seconds < 0:
            raise ValueError("initial_backoff_seconds must be non-negative")
        if self.multiplier < 1:
            raise ValueError("retry multiplier must be at least 1")
        if self.max_backoff_seconds < self.initial_backoff_seconds:
            raise ValueError("max_backoff_seconds must be >= initial_backoff_seconds")

    def backoff_for_attempt(self, attempt: int) -> int:
        """Return delay before the next attempt.

        ``attempt`` is the number of attempts already started. The first failed
        attempt therefore receives ``initial_backoff_seconds``.
        """
        if attempt < 1:
            raise ValueError("retry attempt must be at least 1")
        delay = self.initial_backoff_seconds * (self.multiplier ** (attempt - 1))
        return min(int(delay), self.max_backoff_seconds)


@dataclass(frozen=True)
class RetryPlanResult:
    workflow_id: str
    step_id: str
    attempt: int
    max_attempts: int
    backoff_seconds: int
    retry_not_before: str


@dataclass(frozen=True)
class RetryReleaseResult:
    workflow_id: str
    step_id: str
    attempt: int
    max_attempts: int


class WorkflowRetryService:
    """Persist and release bounded workflow-step retries."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.steps = WorkflowStepRepository(session)
        self.workflows = WorkflowRepository(session)
        self.audit_events = AuditEventRepository(session)
        self.resource_events = ResourceEventRepository(session)

    def plan_bounded_retry(
        self,
        step_id: str,
        *,
        policy: RetryPolicy | None = None,
        now: datetime | None = None,
    ) -> RetryPlanResult:
        step = self.steps.require(step_id)
        selected_policy = policy or RetryPolicy()
        backoff_seconds = selected_policy.backoff_for_attempt(step.attempt)
        return self.plan_retry(step_id, backoff_seconds=backoff_seconds, now=now)

    def plan_retry(
        self,
        step_id: str,
        *,
        backoff_seconds: int,
        now: datetime | None = None,
    ) -> RetryPlanResult:
        step = self.steps.plan_retry(
            step_id,
            backoff_seconds=backoff_seconds,
            now=now,
        )
        workflow = self.workflows.require(step.workflow_id)
        retry_state = dict(step.input.get("_retry") or {})
        retry_not_before = str(retry_state["retry_not_before"])

        workflow.status = {
            **workflow.status,
            "retry_pending": True,
            "retry_step_id": step.id,
            "retry_not_before": retry_not_before,
        }
        workflow.touch_resource_version()

        self.audit_events.append(
            action="workflow.step.retry_planned",
            actor_type="system",
            target_kind="WorkflowStep",
            target_id=step.id,
            workflow_id=step.workflow_id,
            task_id=step.task_id,
            details={
                "attempt": step.attempt,
                "max_attempts": step.max_attempts,
                "backoff_seconds": backoff_seconds,
                "retry_not_before": retry_not_before,
            },
        )
        self.resource_events.append(
            event_type="WorkflowStepRetryPlanned",
            resource_kind="Workflow",
            resource_id=step.workflow_id,
            workflow_id=step.workflow_id,
            task_id=step.task_id,
            resource_version=workflow.resource_version,
            payload={
                "step_id": step.id,
                "step_name": step.name,
                "attempt": step.attempt,
                "max_attempts": step.max_attempts,
                "backoff_seconds": backoff_seconds,
                "retry_not_before": retry_not_before,
            },
        )
        self.session.commit()
        return RetryPlanResult(
            workflow_id=step.workflow_id,
            step_id=step.id,
            attempt=step.attempt,
            max_attempts=step.max_attempts,
            backoff_seconds=backoff_seconds,
            retry_not_before=retry_not_before,
        )

    def release_due_retries(
        self,
        *,
        now: datetime | None = None,
    ) -> list[RetryReleaseResult]:
        current = (now or datetime.now(UTC)).astimezone(UTC)
        results: list[RetryReleaseResult] = []

        for step in self.steps.list_due_retries(now=current):
            previous_task_id = step.task_id
            step = self.steps.release_retry(step.id)
            workflow = self.workflows.require(step.workflow_id)
            workflow.status = {
                **workflow.status,
                "retry_pending": False,
                "retry_step_id": None,
                "retry_not_before": None,
            }
            if workflow.phase == "failed":
                workflow.phase = "queued"
                workflow.status = {**workflow.status, "phase": "queued"}
                workflow.finished_at = None
            workflow.touch_resource_version()

            self.audit_events.append(
                action="workflow.step.retry_released",
                actor_type="system",
                target_kind="WorkflowStep",
                target_id=step.id,
                workflow_id=step.workflow_id,
                task_id=previous_task_id,
                details={
                    "attempt": step.attempt,
                    "max_attempts": step.max_attempts,
                },
            )
            self.resource_events.append(
                event_type="WorkflowStepRetryReleased",
                resource_kind="Workflow",
                resource_id=step.workflow_id,
                workflow_id=step.workflow_id,
                task_id=previous_task_id,
                resource_version=workflow.resource_version,
                payload={
                    "step_id": step.id,
                    "step_name": step.name,
                    "attempt": step.attempt,
                    "max_attempts": step.max_attempts,
                    "phase": workflow.phase,
                },
            )
            results.append(
                RetryReleaseResult(
                    workflow_id=step.workflow_id,
                    step_id=step.id,
                    attempt=step.attempt,
                    max_attempts=step.max_attempts,
                )
            )

        self.session.commit()
        return results
