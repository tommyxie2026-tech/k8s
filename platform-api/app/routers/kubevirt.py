from fastapi import APIRouter
from pydantic import BaseModel

from app.core.executor import executor

router = APIRouter(prefix="/vms", tags=["kubevirt"])


class VMActionRequest(BaseModel):
    namespace: str = "default"
    name: str
    confirm: bool = True


class VMBackupRequest(BaseModel):
    namespace: str = "default"
    name: str
    confirm: bool = False


class VMRestoreRequest(BaseModel):
    name: str
    target_namespace: str = ""
    confirm: bool = False
    confirm_phrase: str = ""


@router.get("")
def list_vms() -> dict[str, str]:
    return {"message": "Use kubectl/virtctl integration in next phase; V1 exposes action endpoints."}


@router.post("/start")
def start_vm(req: VMActionRequest):
    return executor.submit(
        "0070-kubevirt-vm-ops.yml",
        {
            "kubevirt_enabled": True,
            "kubevirt_vm_action": "start",
            "kubevirt_vm_namespace": req.namespace,
            "kubevirt_vm_name": req.name,
        },
    )


@router.post("/stop")
def stop_vm(req: VMActionRequest):
    return executor.submit(
        "0070-kubevirt-vm-ops.yml",
        {
            "kubevirt_enabled": True,
            "kubevirt_vm_action": "stop",
            "kubevirt_vm_namespace": req.namespace,
            "kubevirt_vm_name": req.name,
        },
    )


@router.post("/status")
def status_vm(req: VMActionRequest):
    return executor.submit(
        "0070-kubevirt-vm-ops.yml",
        {
            "kubevirt_enabled": True,
            "kubevirt_vm_action": "status",
            "kubevirt_vm_namespace": req.namespace,
            "kubevirt_vm_name": req.name,
        },
    )


@router.post("/backup")
def backup_vm(req: VMBackupRequest):
    return executor.submit(
        "0095-kubevirt-vm-backup.yml",
        {
            "vm_backup_enabled": True,
            "vm_backup_apply_confirm": req.confirm,
            "vm_backup_namespace": req.namespace,
            "vm_backup_name": req.name,
        },
    )


@router.post("/restore")
def restore_vm(req: VMRestoreRequest):
    return executor.submit(
        "0096-kubevirt-vm-restore.yml",
        {
            "vm_restore_enabled": True,
            "vm_restore_apply_confirm": req.confirm,
            "vm_restore_name": req.name,
            "vm_restore_target_namespace": req.target_namespace,
            "vm_restore_confirm_phrase": req.confirm_phrase,
        },
    )
