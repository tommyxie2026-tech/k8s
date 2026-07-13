from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import TaskModel, TaskPhase
from app.repositories.exceptions import OptimisticConcurrencyError


_TERMINAL_PHASES = {
    TaskPhase.succeeded.value,
    TaskPhase.failed.value,
    TaskPhase.cancelled.value,
}


class TaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, task: TaskModel) -> TaskModel:
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get(self, task_id: str, *, include_deleted: bool = False) -> TaskModel | None:
        stmt = select(TaskModel).where(TaskModel.id == task_id)
        if not include_deleted:
            stmt = stmt.where(TaskModel.deleted_at.is_(None))
        return self.session.scalar(stmt)

    def list(
        self,
        *,
        workflow_id: str | None = None,
        phase: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TaskModel]:
        stmt = select(TaskModel).order_by(TaskModel.created_at.desc()).limit(limit).offset(offset)
        if workflow_id is not None:
            stmt = stmt.where(TaskModel.workflow_id == workflow_id)
        if phase is not None:
            stmt = stmt.where(TaskModel.phase == phase)
        if not include_deleted:
            stmt = stmt.where(TaskModel.deleted_at.is_(None))
        return list(self.session.scalars(stmt))

    def save(self, task: TaskModel, *, expected_resource_version: str | None = None) -> TaskModel:
        if expected_resource_version is not None and task.resource_version != expected_resource_version:
            raise OptimisticConcurrencyError(f"task {task.id} resource_version mismatch")
        task.touch_resource_version()
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def transition(
        self,
        task: TaskModel,
        phase: str,
        *,
        expected_resource_version: str | None = None,
    ) -> TaskModel:
        if task.phase in _TERMINAL_PHASES and phase != task.phase:
            raise ValueError(f"task {task.id} is already terminal: {task.phase}")
        task.phase = phase
        return self.save(task, expected_resource_version=expected_resource_version)

    def soft_delete(self, task: TaskModel, *, expected_resource_version: str | None = None) -> TaskModel:
        if expected_resource_version is not None and task.resource_version != expected_resource_version:
            raise OptimisticConcurrencyError(f"task {task.id} resource_version mismatch")
        task.mark_deleted()
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
