from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ResourceEventModel


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
    ) -> list[ResourceEventModel]:
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
        return list(self.session.scalars(statement))
