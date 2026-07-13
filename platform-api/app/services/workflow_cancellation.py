from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories import AuditEventRepository, ResourceEventRepository
from app.db.workflow_cancellation import (
    WorkflowCancellationRepository,
    WorkflowCancellationResult,
)


class WorkflowCancellationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.cancellations = WorkflowCancellationRepository(session)
        self.audit_events = AuditEventRepository(session)
        self.resource_events = ResourceEventRepository(session)

    def request_cancel(
        self,
        workflow_id: str,
        *,
        reason: str | None = None,
        actor_user_id: str | None = None,
        request_id: str | None = None,
    ) -> WorkflowCancellationResult:
        result = self.cancellations.request_cancel(workflow_id, reason=reason)
        self.audit_events.append(
            action="workflow.cancel.requested",
            actor_user_id=actor_user_id,
            actor_type="user" if actor_user_id else "system",
            target_kind="Workflow",
            target_id=workflow_id,
            workflow_id=workflow_id,
            request_id=request_id,
            details={
                "reason": reason,
                "workflow_phase": result.workflow_phase,
                "cancelled_task_ids": list(result.cancelled_task_ids),
                "cancellation_requested_task_ids": list(
                    result.cancellation_requested_task_ids
                ),
            },
        )
        self.resource_events.append(
            event_type="WorkflowCancellationRequested",
            resource_kind="Workflow",
            resource_id=workflow_id,
            actor_user_id=actor_user_id,
            workflow_id=workflow_id,
            payload={
                "reason": reason,
                "phase": result.workflow_phase,
            },
        )
        self.session.commit()
        return result

    def finalize_cancel(
        self,
        workflow_id: str,
        *,
        actor_user_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        workflow = self.cancellations.finalize_cancel(workflow_id)
        self.audit_events.append(
            action="workflow.cancelled",
            actor_user_id=actor_user_id,
            actor_type="user" if actor_user_id else "system",
            target_kind="Workflow",
            target_id=workflow_id,
            workflow_id=workflow_id,
            request_id=request_id,
        )
        self.resource_events.append(
            event_type="WorkflowCancelled",
            resource_kind="Workflow",
            resource_id=workflow_id,
            actor_user_id=actor_user_id,
            workflow_id=workflow_id,
            resource_version=workflow.resource_version,
            payload={"phase": workflow.phase},
        )
        self.session.commit()
