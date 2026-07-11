from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.task import TaskModel, TaskPhase


class TaskNotFoundError(LookupError):
    """Raised when a Task resource cannot be found."""


class TaskVersionConflictError(RuntimeError):
    """Raised when optimistic concurrency validation fails."""


@dataclass(frozen=True, slots=True)
class TaskCreate:
    name: str
    executor_type: str
    command_ref: str
    spec: dict
    workflow_id: str | None = None


class TaskRepository(Protocol):
    def create(self, data: TaskCreate) -> TaskModel: ...

    def get(self, task_id: str, *, include_deleted: bool = False) -> TaskModel | None: ...

    def list(self, *, phase: TaskPhase | None = None, limit: int = 100, offset: int = 0) -> Sequence[TaskModel]: ...

    def transition(
        self,
        task_id: str,
        *,
        expected_resource_version: str,
        phase: TaskPhase,
        return_code: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
        log_path: str | None = None,
    ) -> TaskModel: ...


class SqlTaskRepository:
    """SQLAlchemy implementation of the frozen Task repository contract."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _new_id() -> str:
        # Temporary compatibility generator. The public contract remains UUIDv7-compatible;
        # replace this with a shared UUIDv7 generator when the runtime baseline supports it.
        return str(uuid4())

    @staticmethod
    def _new_resource_version() -> str:
        return str(uuid4())

    def create(self, data: TaskCreate) -> TaskModel:
        now = datetime.now(timezone.utc)
        task = TaskModel(
            id=self._new_id(),
            name=data.name,
            workflow_id=data.workflow_id,
            executor_type=data.executor_type,
            command_ref=data.command_ref,
            spec=dict(data.spec),
            status={"phase": TaskPhase.queued.value},
            phase=TaskPhase.queued.value,
            generation=1,
            resource_version=self._new_resource_version(),
            created_at=now,
            updated_at=now,
        )
        self._session.add(task)
        self._session.commit()
        self._session.refresh(task)
        return task

    def get(self, task_id: str, *, include_deleted: bool = False) -> TaskModel | None:
        statement: Select[tuple[TaskModel]] = select(TaskModel).where(TaskModel.id == task_id)
        if not include_deleted:
            statement = statement.where(TaskModel.deleted_at.is_(None))
        return self._session.scalar(statement)

    def list(
        self,
        *,
        phase: TaskPhase | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[TaskModel]:
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        if offset < 0:
            raise ValueError("offset must be non-negative")

        statement = select(TaskModel).where(TaskModel.deleted_at.is_(None))
        if phase is not None:
            statement = statement.where(TaskModel.phase == phase.value)
        statement = statement.order_by(TaskModel.created_at.desc()).offset(offset).limit(limit)
        return tuple(self._session.scalars(statement).all())

    def transition(
        self,
        task_id: str,
        *,
        expected_resource_version: str,
        phase: TaskPhase,
        return_code: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
        log_path: str | None = None,
    ) -> TaskModel:
        task = self.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        if task.resource_version != expected_resource_version:
            raise TaskVersionConflictError(task_id)

        terminal = {TaskPhase.succeeded.value, TaskPhase.failed.value, TaskPhase.cancelled.value}
        if task.phase in terminal:
            raise ValueError(f"task {task_id} is already terminal: {task.phase}")

        task.phase = phase.value
        task.status = {**(task.status or {}), "phase": phase.value}
        task.return_code = return_code
        task.stdout = stdout
        task.stderr = stderr
        task.log_path = log_path
        task.resource_version = self._new_resource_version()
        task.updated_at = datetime.now(timezone.utc)

        self._session.add(task)
        self._session.commit()
        self._session.refresh(task)
        return task
