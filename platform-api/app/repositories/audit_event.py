from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditEventModel


class AuditEventRepository:
    """Append-only persistence boundary for audit events."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def append(
        self,
        *,
        actor_type: str,
        action: str,
        result: str = "success",
        actor_user_id: str | None = None,
        target_kind: str | None = None,
        target_id: str | None = None,
        workflow_id: str | None = None,
        task_id: str | None = None,
        request_id: str | None = None,
        source_ip: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditEventModel:
        event = AuditEventModel(
            actor_type=actor_type,
            actor_user_id=actor_user_id,
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
        actor_user_id: str | None = None,
        action: str | None = None,
        target_kind: str | None = None,
        target_id: str | None = None,
        workflow_id: str | None = None,
        task_id: str | None = None,
        result: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEventModel]:
        statement = select(AuditEventModel)
        if actor_user_id is not None:
            statement = statement.where(AuditEventModel.actor_user_id == actor_user_id)
        if action is not None:
            statement = statement.where(AuditEventModel.action == action)
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
        return list(self.session.scalars(statement))
