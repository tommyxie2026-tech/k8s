from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from app.executors.base import ExecutionRequest
from app.executors.registry import executor_registry
from app.models.task import TaskModel, TaskPhase
from app.repositories.task import TaskRepository


class RuntimeService:
    """Owns Task lifecycle and dispatches executor-neutral requests.

    This first vertical slice executes inline. The public boundary is intentionally
    stable so a queue/worker implementation can replace inline execution later
    without changing routers or workflow services.
    """

    def __init__(self, session: Session) -> None:
        self.tasks = TaskRepository(session)

    def submit(
        self,
        *,
        name: str,
        executor_type: str,
        command_ref: str,
        parameters: dict | None = None,
        workflow_id: str | None = None,
    ) -> TaskModel:
        task_id = str(uuid4())
        task = self.tasks.create(
            task_id=task_id,
            name=name,
            workflow_id=workflow_id,
            executor_type=executor_type,
            command_ref=command_ref,
            spec={"parameters": parameters or {}},
        )
        self.tasks.update_phase(task, TaskPhase.queued)
        return task

    def execute(self, task_id: str) -> TaskModel:
        task = self.tasks.get(task_id)
        if task is None:
            raise ValueError(f"task not found: {task_id}")
        if task.phase not in {TaskPhase.pending.value, TaskPhase.queued.value}:
            raise ValueError(f"task {task_id} cannot execute from phase={task.phase}")

        self.tasks.update_phase(task, TaskPhase.running)
        executor = executor_registry.get(task.executor_type)
        request = ExecutionRequest(
            task_id=task.id,
            action=task.name,
            command_ref=task.command_ref,
            parameters=(task.spec or {}).get("parameters", {}),
        )

        try:
            result = executor.execute(request)
        except Exception as exc:
            return self.tasks.update_phase(
                task,
                TaskPhase.failed,
                stderr=f"{type(exc).__name__}: {exc}",
            )

        phase = TaskPhase.succeeded if result.succeeded else TaskPhase.failed
        return self.tasks.update_phase(
            task,
            phase,
            return_code=result.return_code,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def submit_and_execute(self, **kwargs) -> TaskModel:
        task = self.submit(**kwargs)
        return self.execute(task.id)
