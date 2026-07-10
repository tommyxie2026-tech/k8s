from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import TaskModel, TaskPhase


class TaskRepository:
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
            name=name,
            workflow_id=workflow_id,
            executor_type=executor_type,
            command_ref=command_ref,
            spec=spec,
            status={"phase": TaskPhase.pending.value},
            phase=TaskPhase.pending.value,
            resource_version=str(uuid4()),
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get(self, task_id: str) -> TaskModel | None:
        return self.session.get(TaskModel, task_id)

    def list(self, *, limit: int = 100) -> list[TaskModel]:
        statement = select(TaskModel).where(TaskModel.deleted_at.is_(None)).order_by(TaskModel.created_at.desc()).limit(limit)
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
        task.resource_version = str(uuid4())
        task.updated_at = datetime.now(timezone.utc)
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
