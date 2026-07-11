from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import WorkflowModel


class WorkflowRepository:
    """Persistence boundary for Workflow resources.

    Routers, workflow services, and executors must not issue SQL directly.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, workflow: WorkflowModel) -> WorkflowModel:
        self.session.add(workflow)
        self.session.flush()
        self.session.refresh(workflow)
        return workflow

    def get(self, workflow_id: str, *, include_deleted: bool = False) -> WorkflowModel | None:
        statement = select(WorkflowModel).where(WorkflowModel.id == workflow_id)
        if not include_deleted:
            statement = statement.where(WorkflowModel.deleted_at.is_(None))
        return self.session.scalar(statement)

    def list(
        self,
        *,
        phase: str | None = None,
        cluster_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> Sequence[WorkflowModel]:
        statement = select(WorkflowModel)
        if not include_deleted:
            statement = statement.where(WorkflowModel.deleted_at.is_(None))
        if phase is not None:
            statement = statement.where(WorkflowModel.phase == phase)
        if cluster_id is not None:
            statement = statement.where(WorkflowModel.cluster_id == cluster_id)
        statement = statement.order_by(WorkflowModel.created_at.desc()).offset(offset).limit(limit)
        return self.session.scalars(statement).all()

    def save(self, workflow: WorkflowModel) -> WorkflowModel:
        workflow.touch_resource_version()
        self.session.add(workflow)
        self.session.flush()
        self.session.refresh(workflow)
        return workflow

    def soft_delete(self, workflow: WorkflowModel) -> WorkflowModel:
        workflow.mark_deleted()
        self.session.add(workflow)
        self.session.flush()
        self.session.refresh(workflow)
        return workflow
