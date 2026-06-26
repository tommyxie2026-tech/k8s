from enum import Enum
from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class StepStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class WorkflowStep(BaseModel):
    name: str
    action: str
    playbook: str
    extra_vars: dict[str, str | bool] = Field(default_factory=dict)
    status: StepStatus = StepStatus.pending
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""


class WorkflowRecord(BaseModel):
    workflow_id: str
    name: str
    status: WorkflowStatus = WorkflowStatus.pending
    destructive: bool = False
    steps: list[WorkflowStep] = Field(default_factory=list)


class WorkflowCreateRequest(BaseModel):
    name: str
    confirm: bool = False
    confirm_phrase: str = ""
    params: dict[str, str | bool] = Field(default_factory=dict)
