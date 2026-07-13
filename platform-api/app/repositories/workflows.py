from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import WorkflowModel
from app.repositories.exceptions import OptimisticConcurrencyError


class WorkflowRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, workflow: WorkflowModel) -> WorkflowModel:
        self.session.add(workflow)
        self.session.commit()
        self.session.refresh(workflow)
        return workflow

    def get(self, workflow_id: str, *, include_deleted: bool = False) -> WorkflowModel | None:
        stmt = select(WorkflowModel).where(WorkflowModel.id == workflow_id)
        if not include_deleted:
            stmt = stmt.where(WorkflowModel.deleted_at.is_(None))
        return self.session.scalar(stmt)

    def list(self, *, include_deleted: bool = False, limit: int = 100, offset: int = 0) -> list[WorkflowModel]:
        stmt = select(WorkflowModel).order_by(WorkflowModel.created_at.desc()).limit(limit).offset(offset)
        if not include_deleted:
            stmt = stmt.where(WorkflowModel.deleted_at.is_(None))
        return list(self.session.scalars(stmt))

    def save(self, workflow: WorkflowModel, *, expected_resource_version: str | None = None) -> WorkflowModel:
        if expected_resource_version is not None and workflow.resource_version != expected_resource_version:
            raise OptimisticConcurrencyError(
                f"workflow {workflow.id} resource_version mismatch"
            )
        workflow.touch_resource_version()
        self.session.add(workflow)
        self.session.commit()
        self.session.refresh(workflow)
        return workflow

    def soft_delete(self, workflow: WorkflowModel, *, expected_resource_version: str | None = None) -> WorkflowModel:
        if expected_resource_version is not None and workflow.resource_version != expected_resource_version:
            raise OptimisticConcurrencyError(
                f"workflow {workflow.id} resource_version mismatch"
            )
        workflow.mark_deleted()
        self.session.add(workflow)
        self.session.commit()
        self.session.refresh(workflow)
        return workflow
