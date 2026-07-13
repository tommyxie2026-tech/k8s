from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.models import TaskModel, TaskPhase


TERMINAL_TASK_PHASES = {
    TaskPhase.succeeded.value,
    TaskPhase.failed.value,
    TaskPhase.cancelled.value,
}


class TaskNotFoundError(LookupError):
    pass


class InvalidTaskTransitionError(ValueError):
    pass


class TaskRepository:
    """Repository for durable Task resources.

    The repository owns persistence rules only. Execution remains the
    responsibility of the Runtime Plane.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        name: str,
        executor_type: str,
        command_ref: str,
        workflow_id: str | None = None,
        spec: dict[str, Any] | None = None,
        status: dict[str, Any] | None = None,
    ) -> TaskModel:
        task = TaskModel(
            kind="Task",
            name=name,
            workflow_id=workflow_id,
            executor_type=executor_type,
            command_ref=command_ref,
            phase=TaskPhase.pending.value,
            spec=spec or {},
            status=status or {"phase": TaskPhase.pending.value},
        )
        self.session.add(task)
        self.session.flush()
        return task

    def get(self, task_id: str, *, include_deleted: bool = False) -> TaskModel | None:
        stmt = select(TaskModel).where(TaskModel.id == task_id)
        if not include_deleted:
            stmt = stmt.where(TaskModel.deleted_at.is_(None))
        return self.session.scalar(stmt)

    def require(self, task_id: str, *, include_deleted: bool = False) -> TaskModel:
        task = self.get(task_id, include_deleted=include_deleted)
        if task is None:
            raise TaskNotFoundError(f"task not found: {task_id}")
        return task

    def list(
        self,
        *,
        workflow_id: str | None = None,
        phase: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[TaskModel]:
        stmt = select(TaskModel).order_by(TaskModel.created_at.desc()).limit(limit).offset(offset)
        if workflow_id is not None:
            stmt = stmt.where(TaskModel.workflow_id == workflow_id)
        if phase is not None:
            stmt = stmt.where(TaskModel.phase == phase)
        if not include_deleted:
            stmt = stmt.where(TaskModel.deleted_at.is_(None))
        return self.session.scalars(stmt).all()

    def transition(
        self,
        task_id: str,
        phase: TaskPhase | str,
        *,
        return_code: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
        log_path: str | None = None,
    ) -> TaskModel:
        task = self.require(task_id)
        next_phase = phase.value if isinstance(phase, TaskPhase) else phase

        if task.phase in TERMINAL_TASK_PHASES and next_phase != task.phase:
            raise InvalidTaskTransitionError(
                f"terminal task {task_id} cannot transition from {task.phase} to {next_phase}"
            )

        task.phase = next_phase
        task.status = {**task.status, "phase": next_phase}

        if next_phase == TaskPhase.running.value and task.started_at is None:
            task.started_at = utc_now()
        if next_phase in TERMINAL_TASK_PHASES:
            task.finished_at = task.finished_at or utc_now()

        if return_code is not None:
            task.return_code = return_code
        if stdout is not None:
            task.stdout = stdout
        if stderr is not None:
            task.stderr = stderr
        if log_path is not None:
            task.log_path = log_path

        task.touch_resource_version()
        self.session.flush()
        return task

    def soft_delete(self, task_id: str) -> TaskModel:
        task = self.require(task_id)
        task.mark_deleted()
        self.session.flush()
        return task
