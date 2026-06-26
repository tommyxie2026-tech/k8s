import time

from app.schemas.workflows import StepStatus, WorkflowCreateRequest, WorkflowRecord, WorkflowStatus, WorkflowStep
from app.services.executor import executor

_WORKFLOWS: dict[str, WorkflowRecord] = {}


class WorkflowEngine:
    def create(self, req: WorkflowCreateRequest) -> WorkflowRecord:
        workflow_id = f"wf-{int(time.time() * 1000)}"
        record = WorkflowRecord(
            workflow_id=workflow_id,
            name=req.name,
            destructive=self._is_destructive(req.name),
            steps=self._build_steps(req),
        )

        if record.destructive and not req.confirm:
            record.status = WorkflowStatus.failed
            for step in record.steps:
                step.status = StepStatus.skipped
                step.stderr = "blocked by policy: confirm=true is required"
            _WORKFLOWS[workflow_id] = record
            return record

        if req.name in {"restore.vm", "restore.etcd"} and req.confirm_phrase not in {"RESTORE_VM", "RESTORE_ETCD"}:
            record.status = WorkflowStatus.failed
            for step in record.steps:
                step.status = StepStatus.skipped
                step.stderr = "blocked by policy: invalid confirm_phrase"
            _WORKFLOWS[workflow_id] = record
            return record

        _WORKFLOWS[workflow_id] = record
        self.run(workflow_id)
        return _WORKFLOWS[workflow_id]

    def run(self, workflow_id: str) -> WorkflowRecord:
        record = _WORKFLOWS[workflow_id]
        record.status = WorkflowStatus.running
        for step in record.steps:
            step.status = StepStatus.running
            result = executor.run_playbook(step.action, step.playbook, step.extra_vars)
            step.return_code = result.return_code
            step.stdout = result.stdout
            step.stderr = result.stderr
            step.status = StepStatus.succeeded if result.return_code == 0 else StepStatus.failed
            if step.status == StepStatus.failed:
                record.status = WorkflowStatus.failed
                _WORKFLOWS[workflow_id] = record
                return record
        record.status = WorkflowStatus.succeeded
        _WORKFLOWS[workflow_id] = record
        return record

    def get(self, workflow_id: str) -> WorkflowRecord | None:
        return _WORKFLOWS.get(workflow_id)

    def list(self) -> list[WorkflowRecord]:
        return list(_WORKFLOWS.values())

    def _is_destructive(self, name: str) -> bool:
        return name in {
            "backup.etcd",
            "restore.etcd",
            "backup.vm",
            "restore.vm",
            "nodepool.apply_labels",
            "velero.install",
        }

    def _build_steps(self, req: WorkflowCreateRequest) -> list[WorkflowStep]:
        p = req.params
        workflows: dict[str, list[WorkflowStep]] = {
            "cluster.syntax_check": [WorkflowStep(name="syntax-check", action="cluster.syntax_check", playbook="0000-preflight.yml")],
            "governance.full_check": [
                WorkflowStep(name="scheduling", action="governance.scheduling", playbook="0074-scheduling-policy-check.yml", extra_vars={"node_pools_enabled": True}),
                WorkflowStep(name="failure-domain", action="governance.failure_domain", playbook="0076-failure-domain-check.yml", extra_vars={"node_pools_enabled": True}),
                WorkflowStep(name="capacity", action="governance.capacity", playbook="0077-capacity-planning.yml"),
                WorkflowStep(name="admission", action="governance.admission", playbook="0078-cluster-admission-baseline.yml"),
            ],
            "observability.preflight": [WorkflowStep(name="observability-preflight", action="observability.preflight", playbook="0080-observability-preflight.yml", extra_vars={"observability_enabled": True})],
            "backup.etcd": [WorkflowStep(name="etcd-backup", action="backup.etcd", playbook="0090-etcd-backup.yml", extra_vars={"backup_enabled": True, "etcd_backup_enabled": True, "backup_apply_confirm": req.confirm})],
            "backup.vm": [WorkflowStep(name="vm-backup", action="backup.vm", playbook="0095-kubevirt-vm-backup.yml", extra_vars={"vm_backup_enabled": True, "vm_backup_apply_confirm": req.confirm, "vm_backup_namespace": p.get("namespace", "default"), "vm_backup_name": p.get("name", "")})],
            "restore.vm": [WorkflowStep(name="vm-restore", action="restore.vm", playbook="0096-kubevirt-vm-restore.yml", extra_vars={"vm_restore_enabled": True, "vm_restore_apply_confirm": req.confirm, "vm_restore_name": p.get("name", ""), "vm_restore_target_namespace": p.get("target_namespace", ""), "vm_restore_confirm_phrase": req.confirm_phrase})],
        }
        return workflows.get(req.name, [WorkflowStep(name=req.name, action=req.name, playbook=str(p.get("playbook", "0000-preflight.yml")))])


workflow_engine = WorkflowEngine()
