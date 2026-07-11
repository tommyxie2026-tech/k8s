from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import ResourceMixin, utc_now
from app.db.exceptions import ResourceNotFoundError, ResourceVersionConflictError
from app.db.models import AuditEventModel, ResourceEventModel, TaskModel, WorkflowModel
from app.utils.ids import new_resource_version

ResourceT = TypeVar("ResourceT", bound=ResourceMixin)


class ResourceRepository(Generic[ResourceT]):
    model: type[ResourceT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, resource_id: str, *, include_deleted: bool = False) -> ResourceT | None:
        statement = select(self.model).where(self.model.id == resource_id)
        if not include_deleted:
            statement = statement.where(self.model.deleted_at.is_(None))
        return self.session.scalars(statement).first()

    def require(self, resource_id: str, *, include_deleted: bool = False) -> ResourceT:
        resource = self.get(resource_id, include_deleted=include_deleted)
        if resource is None:
            raise ResourceNotFoundError(f"resource not found: {resource_id}")
        return resource

    def add(self, resource: ResourceT) -> ResourceT:
        self.session.add(resource)
        self.session.flush()
        return resource

    def update_spec(
        self,
        resource_id: str,
        spec: dict[str, Any],
        *,
        expected_resource_version: str | None = None,
    ) -> ResourceT:
        resource = self.require(resource_id)
        self._check_resource_version(resource, expected_resource_version)
        resource.spec = spec
        resource.generation += 1
        resource.touch_resource_version()
        self.session.flush()
        return resource

    def update_status(
        self,
        resource_id: str,
        status: dict[str, Any],
        *,
        expected_resource_version: str | None = None,
    ) -> ResourceT:
        resource = self.require(resource_id)
        self._check_resource_version(resource, expected_resource_version)
        resource.status = status
        resource.touch_resource_version()
        self.session.flush()
        return resource

    def soft_delete(
        self,
        resource_id: str,
        *,
        expected_resource_version: str | None = None,
    ) -> ResourceT:
        resource = self.require(resource_id)
        self._check_resource_version(resource, expected_resource_version)
        resource.mark_deleted()
        self.session.flush()
        return resource

    @staticmethod
    def _check_resource_version(resource: ResourceT, expected: str | None) -> None:
        if expected is not None and resource.resource_version != expected:
            raise ResourceVersionConflictError(
                f"resource_version conflict for {resource.id}: expected {expected}, got {resource.resource_version}"
            )


class WorkflowRepository(ResourceRepository[WorkflowModel]):
    model = WorkflowModel

    def create(
        self,
        *,
        name: str,
        spec: dict[str, Any] | None = None,
        status: dict[str, Any] | None = None,
        cluster_id: str | None = None,
        target_kind: str | None = None,
        target_id: str | None = None,
        destructive: bool = False,
        created_by: str | None = None,
        phase: str = "pending",
    ) -> WorkflowModel:
        workflow = WorkflowModel(
            kind="Workflow",
            name=name,
            spec=spec or {},
            status=status or {"phase": phase},
            cluster_id=cluster_id,
            target_kind=target_kind,
            target_id=target_id,
            destructive=destructive,
            created_by=created_by,
            phase=phase,
        )
        return self.add(workflow)

    def set_phase(self, workflow_id: str, phase: str) -> WorkflowModel:
        workflow = self.require(workflow_id)
        workflow.phase = phase
        workflow.status = {**workflow.status, "phase": phase}
        if phase == "running" and workflow.started_at is None:
            workflow.started_at = utc_now()
        if phase in {"succeeded", "failed", "cancelled"}:
            workflow.finished_at = utc_now()
        workflow.touch_resource_version()
        self.session.flush()
        return workflow


class TaskRepository(ResourceRepository[TaskModel]):
    model = TaskModel

    def create(
        self,
        *,
        name: str,
        executor_type: str,
        command_ref: str,
        workflow_id: str | None = None,
        spec: dict[str, Any] | None = None,
        status: dict[str, Any] | None = None,
        phase: str = "pending",
    ) -> TaskModel:
        task = TaskModel(
            kind="Task",
            name=name,
            spec=spec or {},
            status=status or {"phase": phase},
            workflow_id=workflow_id,
            executor_type=executor_type,
            command_ref=command_ref,
            phase=phase,
        )
        return self.add(task)

    def set_phase(
        self,
        task_id: str,
        phase: str,
        *,
        return_code: int | None = None,
        log_path: str | None = None,
    ) -> TaskModel:
        task = self.require(task_id)
        if task.phase in {"succeeded", "failed", "cancelled"} and task.phase != phase:
            raise ResourceVersionConflictError(f"terminal task cannot transition from {task.phase} to {phase}")
        task.phase = phase
        task.status = {**task.status, "phase": phase}
        if return_code is not None:
            task.return_code = return_code
            task.status = {**task.status, "return_code": return_code}
        if log_path is not None:
            task.log_path = log_path
            task.status = {**task.status, "log_path": log_path}
        if phase == "running" and task.started_at is None:
            task.started_at = utc_now()
        if phase in {"succeeded", "failed", "cancelled"}:
            task.finished_at = utc_now()
        task.touch_resource_version()
        self.session.flush()
        return task


class AuditEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def append(
        self,
        *,
        action: str,
        actor_user_id: str | None = None,
        actor_type: str = "system",
        target_kind: str | None = None,
        target_id: str | None = None,
        workflow_id: str | None = None,
        task_id: str | None = None,
        result: str = "success",
        request_id: str | None = None,
        source_ip: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditEventModel:
        event = AuditEventModel(
            actor_user_id=actor_user_id,
            actor_type=actor_type,
            action=action,
            target_kind=target_kind,
            target_id=target_id,
            workflow_id=workflow_id,
            task_id=task_id,
            result=result,
            request_id=request_id,
            source_ip=source_ip,
            details=details or {},
        )
        self.session.add(event)
        self.session.flush()
        return event


class ResourceEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def append(
        self,
        *,
        event_type: str,
        resource_kind: str,
        resource_id: str,
        actor_user_id: str | None = None,
        workflow_id: str | None = None,
        task_id: str | None = None,
        generation: int | None = None,
        resource_version: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> ResourceEventModel:
        event = ResourceEventModel(
            event_type=event_type,
            resource_kind=resource_kind,
            resource_id=resource_id,
            actor_user_id=actor_user_id,
            workflow_id=workflow_id,
            task_id=task_id,
            generation=generation,
            resource_version=resource_version,
            payload=payload or {},
        )
        self.session.add(event)
        self.session.flush()
        return event


def bump_resource_version(resource: ResourceMixin) -> None:
    resource.resource_version = new_resource_version()
    resource.updated_at = utc_now()
