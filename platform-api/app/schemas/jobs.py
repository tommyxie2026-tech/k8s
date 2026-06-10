from enum import Enum
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus
    action: str


class JobRecord(BaseModel):
    job_id: str
    action: str
    status: JobStatus
    command: list[str] = Field(default_factory=list)
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""
