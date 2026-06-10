import subprocess
import time
from pathlib import Path

from app.core.config import settings
from app.schemas.jobs import JobRecord, JobStatus

_JOBS: dict[str, JobRecord] = {}


class Executor:
    def __init__(self) -> None:
        self.project_root = Path(settings.project_root).resolve()

    def run_playbook(self, action: str, playbook: str, extra_vars: dict[str, str | bool] | None = None) -> JobRecord:
        job_id = f"job-{int(time.time() * 1000)}"
        cmd = [settings.ansible_playbook_bin, "-i", settings.inventory, playbook]
        for key, value in (extra_vars or {}).items():
            cmd.extend(["-e", f"{key}={value}"])

        record = JobRecord(job_id=job_id, action=action, status=JobStatus.running, command=cmd)
        _JOBS[job_id] = record

        proc = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, check=False)
        record.return_code = proc.returncode
        record.stdout = proc.stdout
        record.stderr = proc.stderr
        record.status = JobStatus.succeeded if proc.returncode == 0 else JobStatus.failed
        _JOBS[job_id] = record
        return record

    def get_job(self, job_id: str) -> JobRecord | None:
        return _JOBS.get(job_id)

    def list_jobs(self) -> list[JobRecord]:
        return list(_JOBS.values())


executor = Executor()
