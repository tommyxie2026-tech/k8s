import subprocess
import time
from pathlib import Path

from app.core.config import settings
from app.schemas.workflows import StepStatus, WorkflowRecord, WorkflowStatus, WorkflowStep
from app.services.audit import audit
from app.services.workflow_store import workflow_store


class WorkflowService:
    def __init__(self) -> None:
        self.project_root = Path(getattr(settings, "project_root", ".")).resolve()
        self.ansible_bin = getattr(settings, "ansible_playbook_bin", "ansible-playbook")
        self.inventory = getattr(settings, "inventory", "inventories/hosts-container.yml")

    def run(self, name: str, steps: list[WorkflowStep], destructive: bool = False) -> WorkflowRecord:
        workflow_id = f"wf-{int(time.time() * 1000)}"
        record = WorkflowRecord(workflow_id=workflow_id, name=name, status=WorkflowStatus.running, destructive=destructive, steps=steps)
        workflow_store.save(record)
        audit("workflow.created", workflow_id=workflow_id, name=name, destructive=destructive)

        for idx, step in enumerate(record.steps):
            step.status = StepStatus.running
            workflow_store.save(record)
            audit("workflow.step.running", workflow_id=workflow_id, step=step.name, playbook=step.playbook)

            cmd = [self.ansible_bin, "-i", self.inventory, step.playbook]
            for key, value in step.extra_vars.items():
                cmd.extend(["-e", f"{key}={value}"])

            proc = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, check=False)
            step.return_code = proc.returncode
            step.stdout = proc.stdout
            step.stderr = proc.stderr
            step.status = StepStatus.succeeded if proc.returncode == 0 else StepStatus.failed
            record.steps[idx] = step
            workflow_store.save(record)
            audit("workflow.step.finished", workflow_id=workflow_id, step=step.name, status=step.status, return_code=proc.returncode)

            if proc.returncode != 0:
                record.status = WorkflowStatus.failed
                workflow_store.save(record)
                audit("workflow.failed", workflow_id=workflow_id, failed_step=step.name)
                return record

        record.status = WorkflowStatus.succeeded
        workflow_store.save(record)
        audit("workflow.succeeded", workflow_id=workflow_id)
        return record

    def get(self, workflow_id: str) -> WorkflowRecord | None:
        return workflow_store.get(workflow_id)

    def list(self) -> list[WorkflowRecord]:
        return workflow_store.list()


workflow_service = WorkflowService()
