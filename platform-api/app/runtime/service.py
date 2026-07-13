from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.db.exceptions import ResourceVersionConflictError
from app.db.models import TaskModel, TaskPhase
from app.db.repositories import TaskRepository
from app.runtime.executor import ExecutionRequest, ExecutorRegistry, default_executor_registry


class TaskNotFoundError(LookupError):
    """Raised when Runtime cannot resolve a durable Task resource."""


class TaskNotExecutableError(ValueError):
    """Raised when a Task cannot be executed from its current lifecycle phase."""


@dataclass(frozen=True, slots=True)
class TaskSubmission:
    """Canonical input for creating one durable execution Task."""

    name: str
    executor_type: str
    command_ref: str
    extra_vars: dict[str, Any]
    workflow_id: str | None = None
    timeout_seconds: int | None = None


class RuntimeService:
    """Runtime Plane service for durable Task submission and execution.

    API and Workflow layers submit Task resources through this service. Executor
    implementations remain behind ExecutorRegistry and never own durable state.
    """

    def __init__(
        self,
        session: Session,
        registry: ExecutorRegistry | None = None,
    ) -> None:
        self.session = session
        self.tasks = TaskRepository(session)
        self.registry = registry or default_executor_registry()

    def submit(self, submission: TaskSubmission) -> TaskModel:
        """Create a durable queued Task without executing it in the caller request."""

        task = self.tasks.create(
            name=submission.name,
            executor_type=submission.executor_type,
            command_ref=submission.command_ref,
            workflow_id=submission.workflow_id,
            spec={
                "extra_vars": submission.extra_vars,
                "timeout_seconds": submission.timeout_seconds,
            },
            phase=TaskPhase.queued.value,
        )
        self.session.commit()
        self.session.refresh(task)
        return task

    def execute(self, task_id: str) -> TaskModel:
        """Execute one queued Task and persist terminal state.

        This method is intended for a worker loop. It is deliberately separate
        from submit() so API requests do not need to block on infrastructure work.
        """

        task = self.tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"task not found: {task_id}")
        if task.phase not in {TaskPhase.pending.value, TaskPhase.queued.value}:
            raise TaskNotExecutableError(
                f"task {task.id} cannot execute from phase {task.phase}"
            )

        self.tasks.set_phase(task.id, TaskPhase.running.value)
        self.session.commit()

        executor = self.registry.get(task.executor_type)
        request = ExecutionRequest(
            task_id=task.id,
            executor_type=task.executor_type,
            command_ref=task.command_ref,
            extra_vars=dict((task.spec or {}).get("extra_vars", {})),
            timeout_seconds=(task.spec or {}).get("timeout_seconds"),
        )

        try:
            result = executor.execute(request)
        except Exception as exc:
            # Preserve diagnostic information while keeping Executor exceptions
            # behind the Runtime boundary.
            failed = self.tasks.fail(task.id, error=str(exc))
            self.session.commit()
            self.session.refresh(failed)
            return failed

        completed = self.tasks.complete(
            task.id,
            return_code=result.return_code,
            stdout=result.stdout,
            stderr=result.stderr,
            log_path=None,
        )
        self.session.commit()
        self.session.refresh(completed)
        return completed

    def cancel(self, task_id: str) -> TaskModel:
        """Cancel a Task that has not reached a terminal state.

        Process signalling for an already-running subprocess is deferred to the
        worker cancellation contract. This method persists the requested state.
        """

        task = self.tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"task not found: {task_id}")
        try:
            cancelled = self.tasks.set_phase(task.id, TaskPhase.cancelled.value)
            self.session.commit()
            self.session.refresh(cancelled)
            return cancelled
        except ResourceVersionConflictError as exc:
            self.session.rollback()
            raise TaskNotExecutableError(str(exc)) from exc
