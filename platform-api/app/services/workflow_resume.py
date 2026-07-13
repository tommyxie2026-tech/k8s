from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.repositories import AuditEventRepository, ResourceEventRepository, WorkflowRepository
from app.db.workflow_steps import WorkflowStepRepository


@dataclass(frozen=True)
class WorkflowResumeResult:
    workflow_id: str
    resume_step_id: str
    reset_step_ids: tuple[str, ...]
    preserved_step_ids: tuple[str, ...]


class WorkflowResumeService:
    """Resume a failed workflow from a selected failed step.

    Resume is intentionally conservative:

    * only failed workflows may be resumed;
    * the selected step must belong to the workflow and be failed;
    * previously succeeded steps are preserved;
    * the selected step and all later non-succeeded steps are reset to pending;
    * old Task bindings and terminal execution details are cleared;
    * retry and compensation activity must not be pending.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.workflows = WorkflowRepository(session)
        self.steps = WorkflowStepRepository(session)
        self.audit_events = AuditEventRepository(session)
        self.resource_events = ResourceEventRepository(session)

    def resume_from_step(
        self,
        workflow_id: str,
        step_id: str,
        *,
        actor_user_id: str | None = None,
    ) -> WorkflowResumeResult:
        workflow = self.workflows.require(workflow_id)
        if workflow.phase != "failed":
            raise ValueError(f"workflow resume requires failed phase, got {workflow.phase}")
        if workflow.status.get("retry_pending"):
            raise ValueError("workflow cannot resume while a retry is pending")
        if workflow.status.get("compensation_phase") in {"pending", "running"}:
            raise ValueError("workflow cannot resume while compensation is active")

        selected = self.steps.require(step_id)
        if selected.workflow_id != workflow_id:
            raise ValueError(f"workflow step {step_id} does not belong to workflow {workflow_id}")
        if selected.phase != "failed":
            raise ValueError(f"workflow resume step must be failed, got {selected.phase}")

        reset_step_ids: list[str] = []
        preserved_step_ids: list[str] = []
        now = utc_now()

        for step in self.steps.list_for_workflow(workflow_id):
            if step.position < selected.position or step.phase == "succeeded":
                preserved_step_ids.append(step.id)
                continue

            step.phase = "pending"
            step.task_id = None
            step.error = None
            step.started_at = None
            step.finished_at = None
            step.updated_at = now
            step.input = {
                **step.input,
                "_resume": {
                    "resumed_from_step_id": selected.id,
                    "previous_attempt": step.attempt,
                    "resumed_at": now,
                },
            }
            reset_step_ids.append(step.id)

        workflow.phase = "queued"
        workflow.finished_at = None
        workflow.status = {
            **workflow.status,
            "phase": "queued",
            "resume_pending": True,
            "resume_step_id": selected.id,
            "resumed_at": now,
        }
        workflow.touch_resource_version()

        self.audit_events.append(
            action="workflow.resumed",
            actor_user_id=actor_user_id,
            actor_type="user" if actor_user_id else "system",
            target_kind="Workflow",
            target_id=workflow.id,
            workflow_id=workflow.id,
            details={
                "resume_step_id": selected.id,
                "reset_step_ids": reset_step_ids,
                "preserved_step_ids": preserved_step_ids,
            },
        )
        self.resource_events.append(
            event_type="WorkflowResumed",
            resource_kind="Workflow",
            resource_id=workflow.id,
            actor_user_id=actor_user_id,
            workflow_id=workflow.id,
            resource_version=workflow.resource_version,
            payload={
                "resume_step_id": selected.id,
                "reset_step_ids": reset_step_ids,
                "preserved_step_ids": preserved_step_ids,
                "phase": workflow.phase,
            },
        )
        self.session.commit()

        return WorkflowResumeResult(
            workflow_id=workflow.id,
            resume_step_id=selected.id,
            reset_step_ids=tuple(reset_step_ids),
            preserved_step_ids=tuple(preserved_step_ids),
        )
