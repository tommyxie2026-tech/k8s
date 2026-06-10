from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    cancelled = "cancelled"


class TaskCreateResponse(BaseModel):
    task_id: str
    status: TaskStatus
    playbook: str


class TaskInfo(BaseModel):
    task_id: str
    status: TaskStatus
    playbook: str
    command: list[str]
    return_code: Optional[int] = None
    extra_vars: Dict[str, Any] = Field(default_factory=dict)


class ConfirmRequest(BaseModel):
    confirm: bool = False
    confirm_phrase: Optional[str] = None


class MessageResponse(BaseModel):
    message: str
