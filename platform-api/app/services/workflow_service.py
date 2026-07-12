from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.db.exceptions import ResourceVersionConflictError
from app.db.models import WorkflowModel, WorkflowStepModel
from app.db.repositories import WorkflowRepository
from app.db.workflow_repositories import WorkflowStepRepository


WORKFLOW_TERMINAL_PHASES = {"succeeded", "failed", "cancelled"}
WORKFLOW_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"queued", "cancelled"},
    "queued": {"running", "cancelled"},
    "running": {"succeeded", "failed", "cancelled"},
    "succeeded": set(),
    "failed": set(),
    "cancelled": set(),
}


class WorkflowService:
    """Application service for durable workflow state and orchestration metadata.

    This service never executes infrastructure commands. Runtime workers create
    and execute Task resources, then report step results back through this
    service.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.workflows = WorkflowRepository(session)
        self.steps = WorkflowStepRepository(session)

    def create(
        self,
        *,
        name: str,
        steps: list[dict[str, Any]],
        destructive: bool = False,
        cluster_id: str | None = None,
        target_kind: str | None = None,
        target_id: str | None = None,
        created_by: str | None = None,
        spec: dict[str, Any] | None = None,
    ) -> tuple[WorkflowModel, list[WorkflowStepModel]]:
        if not name.strip():
            raise ValueError("workflow name must not be empty")
        self._validate_steps(steps)

        workflow = self.workflows.create(
            name=name,
            cluster_id=cluster_id,
            target_kind=target_kind,
            target_id=target_id,
            destructive=destructive,
            created_by=created_by,
            phase="pending",
            spec={
                **(spec or {}),
                "destructive": destructive,
                "step_count": len(steps),
            },
            status={"phase": "pending", "completed_steps": 0, "failed_step": None},
        )
        step_records = self.steps.create_many(workflow.id, steps)
        self.session.commit()
        self.session.refresh(workflow)
        return workflow, step_records

    def list_steps(self, workflow_id: str) -> list[WorkflowStepModel]:
        self.workflows.require(workflow_id)
        return self.steps.list_for_workflow(workflow_id)

    def transition(self, workflow_id: str, phase: str) -> WorkflowModel:
        workflow = self.workflows.require(workflow_id)
        allowed = WORKFLOW_TRANSITIONS.get(workflow.phase, set())
        if phase not in allowed:
            raise ResourceVersionConflictError(
                f"invalid workflow transition from {workflow.phase} to {phase}"
            )
        workflow = self.workflows.set_phase(workflow_id, phase)
        self.session.commit()
        self.session.refresh(workflow)
        return workflow

    def queue(self, workflow_id: str) -> WorkflowModel:
        return self.transition(workflow_id, "queued")

    def start(self, workflow_id: str) -> WorkflowModel:
        return self.transition(workflow_id, "running")

    def mark_step_running(self, workflow_id: str, step_id: str, task_id: str) -> WorkflowStepModel:
        workflow = self.workflows.require(workflow_id)
        if workflow.phase != "running":
            raise ResourceVersionConflictError(
                f"workflow {workflow_id} must be running before a step can start"
            )

        step = self.steps.require(step_id)
        if step.workflow_id != workflow_id:
            raise ValueError(f"step {step_id} does not belong to workflow {workflow_id}")
        self._validate_dependencies_satisfied(workflow_id, step)

        step = self.steps.set_phase(step_id, "running", task_id=task_id)
        self.session.commit()
        self.session.refresh(step)
        return step

    def mark_step_succeeded(self, workflow_id: str, step_id: str) -> WorkflowStepModel:
        workflow = self.workflows.require(workflow_id)
        step = self._require_owned_step(workflow_id, step_id)
        if step.phase != "running":
            raise ResourceVersionConflictError(
                f"workflow step {step_id} must be running before success"
            )

        step = self.steps.set_phase(step_id, "succeeded")
        all_steps = self.steps.list_for_workflow(workflow_id)
        completed = sum(item.phase == "succeeded" for item in all_steps)
        workflow.status = {
            **workflow.status,
            "completed_steps": completed,
            "failed_step": None,
        }
        workflow.touch_resource_version()

        if all(item.phase == "succeeded" for item in all_steps):
            self.workflows.set_phase(workflow_id, "succeeded")

        self.session.commit()
        self.session.refresh(step)
        return step

    def mark_step_failed(
        self,
        workflow_id: str,
        step_id: str,
        *,
        error: str,
    ) -> WorkflowStepModel:
        workflow = self.workflows.require(workflow_id)
        step = self._require_owned_step(workflow_id, step_id)
        if step.phase not in {"running", "queued"}:
            raise ResourceVersionConflictError(
                f"workflow step {step_id} cannot fail from phase={step.phase}"
            )

        step = self.steps.set_phase(step_id, "failed", error=error)
        workflow.status = {
            **workflow.status,
            "phase": "failed",
            "failed_step": step.name,
            "error": error,
        }
        self.workflows.set_phase(workflow_id, "failed")
        self.session.commit()
        self.session.refresh(step)
        return step

    def get(self, workflow_id: str) -> WorkflowModel | None:
        return self.workflows.get(workflow_id)

    @staticmethod
    def _validate_steps(steps: list[dict[str, Any]]) -> None:
        if not steps:
            raise ValueError("workflow must contain at least one step")

        names: set[str] = set()
        for step in steps:
            name = str(step.get("name", "")).strip()
            command_ref = str(step.get("command_ref", "")).strip()
            if not name:
                raise ValueError("workflow step name must not be empty")
            if name in names:
                raise ValueError(f"duplicate workflow step name: {name}")
            if not command_ref:
                raise ValueError(f"workflow step {name} command_ref must not be empty")
            unknown_dependencies = set(step.get("depends_on") or []) - names
            if unknown_dependencies:
                raise ValueError(
                    f"workflow step {name} has unknown or forward dependencies: "
                    f"{sorted(unknown_dependencies)}"
                )
            names.add(name)

    def _validate_dependencies_satisfied(
        self,
        workflow_id: str,
        step: WorkflowStepModel,
    ) -> None:
        if not step.depends_on:
            return
        by_name = {item.name: item for item in self.steps.list_for_workflow(workflow_id)}
        unsatisfied = [
            name
            for name in step.depends_on
            if name not in by_name or by_name[name].phase != "succeeded"
        ]
        if unsatisfied:
            raise ResourceVersionConflictError(
                f"workflow step {step.name} has unsatisfied dependencies: {sorted(unsatisfied)}"
            )

    def _require_owned_step(self, workflow_id: str, step_id: str) -> WorkflowStepModel:
        step = self.steps.require(step_id)
        if step.workflow_id != workflow_id:
            raise ValueError(f"step {step_id} does not belong to workflow {workflow_id}")
        return step
