from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.db.models import TaskModel
from app.db.repositories import TaskRepository
from app.runtime.executor import ExecutorRegistry, default_executor_registry


class TaskService:
    """Application service for durable queued Task resources.

    The service owns Task creation and queue-state semantics. It deliberately
    does not execute commands; execution belongs to the Runtime worker.
    """

    def __init__(
        self,
        session: Session,
        *,
        executor_registry: ExecutorRegistry | None = None,
    ) -> None:
        self.session = session
        self.tasks = TaskRepository(session)
        self.executor_registry = executor_registry or default_executor_registry()

    def enqueue(
        self,
        *,
        name: str,
        executor_type: str,
        command_ref: str,
        workflow_id: str | None = None,
        extra_vars: dict[str, Any] | None = None,
        timeout_seconds: int | None = None,
    ) -> TaskModel:
        """Create a durable queued task without invoking the executor."""
        if not name.strip():
            raise ValueError("task name must not be empty")
        if timeout_seconds is not None and timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        # Validate executor registration at submission time so unsupported task
        # types do not enter the durable queue.
        self.executor_registry.get(executor_type)

        task = self.tasks.create(
            name=name,
            executor_type=executor_type,
            command_ref=command_ref,
            workflow_id=workflow_id,
            phase="queued",
            spec={
                "executor_type": executor_type,
                "command_ref": command_ref,
                "extra_vars": extra_vars or {},
                "timeout_seconds": timeout_seconds,
            },
            status={"phase": "queued"},
        )
        self.session.commit()
        self.session.refresh(task)
        return task

    def get(self, task_id: str) -> TaskModel | None:
        return self.tasks.get(task_id)

    def require(self, task_id: str) -> TaskModel:
        return self.tasks.require(task_id)
