from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditEventModel, ResourceEventModel


class AuditEventRepository:
    """Append-only persistence boundary for audit events."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def append(
        self,
        *,
        action: str,
        actor_type: str = "system",
        actor_user_id: str | None = None,
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
        self.session.commit()
        self.session.refresh(event)
        return event

    def get(self, event_id: str) -> AuditEventModel | None:
        return self.session.get(AuditEventModel, event_id)

    def list(
        self,
        *,
        action: str | None = None,
        actor_user_id: str | None = None,
        target_kind: str | None = None,
        target_id: str | None = None,
        workflow_id: str | None = None,
        task_id: str | None = None,
        result: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AuditEventModel]:
        statement = select(AuditEventModel)
        if action is not None:
            statement = statement.where(AuditEventModel.action == action)
        if actor_user_id is not None:
            statement = statement.where(AuditEventModel.actor_user_id == actor_user_id)
        if target_kind is not None:
            statement = statement.where(AuditEventModel.target_kind == target_kind)
        if target_id is not None:
            statement = statement.where(AuditEventModel.target_id == target_id)
        if workflow_id is not None:
            statement = statement.where(AuditEventModel.workflow_id == workflow_id)
        if task_id is not None:
            statement = statement.where(AuditEventModel.task_id == task_id)
        if result is not None:
            statement = statement.where(AuditEventModel.result == result)
        statement = statement.order_by(AuditEventModel.created_at.desc()).offset(offset).limit(limit)
        return self.session.scalars(statement).all()


class ResourceEventRepository:
    """Append-only persistence boundary for resource lifecycle events."""

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
        self.session.commit()
        self.session.refresh(event)
        return event

    def get(self, event_id: str) -> ResourceEventModel | None:
        return self.session.get(ResourceEventModel, event_id)

    def list(
        self,
        *,
        event_type: str | None = None,
        resource_kind: str | None = None,
        resource_id: str | None = None,
        workflow_id: str | None = None,
        task_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ResourceEventModel]:
        statement = select(ResourceEventModel)
        if event_type is not None:
            statement = statement.where(ResourceEventModel.event_type == event_type)
        if resource_kind is not None:
            statement = statement.where(ResourceEventModel.resource_kind == resource_kind)
        if resource_id is not None:
            statement = statement.where(ResourceEventModel.resource_id == resource_id)
        if workflow_id is not None:
            statement = statement.where(ResourceEventModel.workflow_id == workflow_id)
        if task_id is not None:
            statement = statement.where(ResourceEventModel.task_id == task_id)
        statement = statement.order_by(ResourceEventModel.created_at.desc()).offset(offset).limit(limit)
        return self.session.scalars(statement).all()
