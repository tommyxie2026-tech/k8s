import time

from app.schemas.workflows import WorkflowCreateRequest, WorkflowRecord, WorkflowStatus, WorkflowStep, StepStatus
from app.services.audit import audit
from app.services.executor import executor
from app.services.workflow_store import workflow_store


WORKFLOW_TEMPLATES: dict[str, dict] = {
    "governance.full_check": {
        "destructive": False,
        "steps": [
            ("scheduling", "0074-scheduling-policy-check.yml", {"node_pools_enabled": True}),
            ("storageclass", "0075-storageclass-governance.yml", {"storage_pools_enabled": True}),
            ("failure-domain", "0076-failure-domain-check.yml", {"node_pools_enabled": True}),
            ("capacity", "0077-capacity-planning.yml", {}),
            ("admission", "0078-cluster-admission-baseline.yml", {}),
        ],
    },
    "backup.vm": {
        "destructive": False,
        "steps": [
            ("velero-preflight", "0092-velero-preflight.yml", {}),
            ("snapshot-check", "0094-volume-snapshot-check.yml", {}),
            ("vm-backup", "0095-kubevirt-vm-backup.yml", {}),
        ],
    },
    "restore.vm": {
        "destructive": True,
        "confirm_phrase": "RESTORE_VM",
        "steps": [
            ("velero-preflight", "0092-velero-preflight.yml", {}),
            ("snapshot-check", "0094-volume-snapshot-check.yml", {}),
            ("vm-restore", "0096-kubevirt-vm-restore.yml", {}),
        ],
    },
    "observability.preflight": {
        "destructive": False,
        "steps": [
            ("observability-preflight", "0080-observability-preflight.yml", {"observability_enabled": True}),
        ],
    },
}


class WorkflowEngine:
    def create(self, request: WorkflowCreateRequest) -> WorkflowRecord:
        if request.name not in WORKFLOW_TEMPLATES:
            raise ValueError(f"unknown workflow: {request.name}")

        template = WORKFLOW_TEMPLATES[request.name]
        destructive = bool(template.get("destructive", False))
        if destructive:
            required_phrase = template.get("confirm_phrase", "CONFIRM")
            if not request.confirm or request.confirm_phrase != required_phrase:
                audit("workflow.rejected", name=request.name, reason="missing destructive confirmation")
                raise PermissionError(f"workflow {request.name} requires confirm=true and confirm_phrase={required_phrase}")

        workflow_id = f"wf-{int(time.time() * 1000)}"
        steps: list[WorkflowStep] = []
        for step_name, playbook, defaults in template["steps"]:
            extra_vars = dict(defaults)
            extra_vars.update(request.params)
            steps.append(WorkflowStep(name=step_name, action=f"{request.name}.{step_name}", playbook=playbook, extra_vars=extra_vars))

        record = WorkflowRecord(workflow_id=workflow_id, name=request.name, destructive=destructive, steps=steps)
        workflow_store.save(record)
        audit("workflow.created", workflow_id=workflow_id, name=request.name, destructive=destructive)
        self.run(workflow_id)
        return workflow_store.get(workflow_id) or record

    def run(self, workflow_id: str) -> WorkflowRecord:
        record = workflow_store.get(workflow_id)
        if record is None:
            raise ValueError(f"workflow not found: {workflow_id}")

        record.status = WorkflowStatus.running
        workflow_store.save(record)
        audit("workflow.running", workflow_id=workflow_id, name=record.name)

        for step in record.steps:
            step.status = StepStatus.running
            workflow_store.save(record)
            audit("workflow.step.running", workflow_id=workflow_id, step=step.name, playbook=step.playbook)

            job = executor.run_playbook(step.action, step.playbook, step.extra_vars)
            step.return_code = job.return_code
            step.stdout = job.stdout
            step.stderr = job.stderr
            if job.return_code == 0:
                step.status = StepStatus.succeeded
                audit("workflow.step.succeeded", workflow_id=workflow_id, step=step.name)
            else:
                step.status = StepStatus.failed
                record.status = WorkflowStatus.failed
                workflow_store.save(record)
                audit("workflow.failed", workflow_id=workflow_id, failed_step=step.name, return_code=job.return_code)
                return record

            workflow_store.save(record)

        record.status = WorkflowStatus.succeeded
        workflow_store.save(record)
        audit("workflow.succeeded", workflow_id=workflow_id)
        return record

    def get(self, workflow_id: str) -> WorkflowRecord | None:
        return workflow_store.get(workflow_id)

    def list(self) -> list[WorkflowRecord]:
        return workflow_store.list()


workflow_engine = WorkflowEngine()
