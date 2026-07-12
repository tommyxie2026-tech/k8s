from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.models import TaskModel, TaskPhase
from app.utils.ids import new_resource_version


class TaskRepository:
    """Persistence boundary for canonical Task resources."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        task_id: str,
        name: str,
        executor_type: str,
        command_ref: str,
        spec: dict,
        workflow_id: str | None = None,
    ) -> TaskModel:
        task = TaskModel(
            id=task_id,
            kind="Task",
            name=name,
            workflow_id=workflow_id,
            executor_type=executor_type,
            command_ref=command_ref,
            spec=spec,
            status={"phase": TaskPhase.pending.value},
            phase=TaskPhase.pending.value,
            resource_version=new_resource_version(),
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get(self, task_id: str, *, include_deleted: bool = False) -> TaskModel | None:
        statement = select(TaskModel).where(TaskModel.id == task_id)
        if not include_deleted:
            statement = statement.where(TaskModel.deleted_at.is_(None))
        return self.session.scalar(statement)

    def list(
        self,
        *,
        phase: TaskPhase | None = None,
        workflow_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[TaskModel]:
        statement = select(TaskModel)
        if not include_deleted:
            statement = statement.where(TaskModel.deleted_at.is_(None))
        if phase is not None:
            statement = statement.where(TaskModel.phase == phase.value)
        if workflow_id is not None:
            statement = statement.where(TaskModel.workflow_id == workflow_id)
        statement = statement.order_by(TaskModel.created_at.desc()).offset(offset).limit(limit)
        return list(self.session.scalars(statement))

    def update_phase(
        self,
        task: TaskModel,
        phase: TaskPhase,
        *,
        return_code: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
        log_path: str | None = None,
    ) -> TaskModel:
        task.phase = phase.value
        task.status = {**(task.status or {}), "phase": phase.value}
        task.return_code = return_code
        task.stdout = stdout
        task.stderr = stderr
        task.log_path = log_path
        if phase == TaskPhase.running and task.started_at is None:
            task.started_at = utc_now()
        if phase in {TaskPhase.succeeded, TaskPhase.failed, TaskPhase.cancelled}:
            task.finished_at = utc_now()
        task.touch_resource_version()
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def soft_delete(self, task: TaskModel) -> TaskModel:
        task.mark_deleted()
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
