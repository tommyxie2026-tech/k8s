from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.task import TaskModel
from app.schemas.common import TaskInfo
from app.schemas.jobs import JobRecord


class ResourceMetadata(BaseModel):
    id: str
    kind: str
    name: str
    labels: dict[str, Any] = Field(default_factory=dict)
    annotations: dict[str, Any] = Field(default_factory=dict)
    generation: int
    resource_version: str
    created_at: str
    updated_at: str
    deleted_at: str | None = None


class TaskResource(BaseModel):
    metadata: ResourceMetadata
    spec: dict[str, Any] = Field(default_factory=dict)
    status: dict[str, Any] = Field(default_factory=dict)


class TaskCompatibilityResponse(BaseModel):
    """Compatibility response for legacy /jobs routes.

    New implementation should use TaskResource. Legacy clients can still read
    task_id/status/playbook/action-like fields during M2 convergence.
    """

    task_id: str
    status: str
    command_ref: str
    executor_type: str = "ansible"
    workflow_id: str | None = None
    return_code: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    log_path: str | None = None


def _dt(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def task_model_to_resource(task: TaskModel) -> TaskResource:
    return TaskResource(
        metadata=ResourceMetadata(
            id=task.id,
            kind=task.kind,
            name=task.name,
            labels={},
            annotations={},
            generation=task.generation,
            resource_version=task.resource_version,
            created_at=str(task.created_at),
            updated_at=str(task.updated_at),
            deleted_at=_dt(task.deleted_at),
        ),
        spec={
            **(task.spec or {}),
            "workflow_id": task.workflow_id,
            "executor_type": task.executor_type,
            "command_ref": task.command_ref,
        },
        status={
            **(task.status or {}),
            "phase": task.phase,
            "return_code": task.return_code,
            "stdout": task.stdout,
            "stderr": task.stderr,
            "log_path": task.log_path,
        },
    )


def task_model_to_compatibility_response(task: TaskModel) -> TaskCompatibilityResponse:
    return TaskCompatibilityResponse(
        task_id=task.id,
        status=task.phase,
        command_ref=task.command_ref,
        executor_type=task.executor_type,
        workflow_id=task.workflow_id,
        return_code=task.return_code,
        stdout=task.stdout,
        stderr=task.stderr,
        log_path=task.log_path,
    )


def legacy_task_info_to_compatibility_response(task: TaskInfo) -> TaskCompatibilityResponse:
    return TaskCompatibilityResponse(
        task_id=task.task_id,
        status=task.status.value,
        command_ref=task.playbook,
        executor_type="ansible",
        return_code=task.return_code,
    )


def job_record_to_compatibility_response(job: JobRecord) -> TaskCompatibilityResponse:
    command_ref = job.command[-1] if job.command else job.action
    return TaskCompatibilityResponse(
        task_id=job.job_id,
        status=job.status.value,
        command_ref=command_ref,
        executor_type="ansible",
        return_code=job.return_code,
        stdout=job.stdout,
        stderr=job.stderr,
    )
