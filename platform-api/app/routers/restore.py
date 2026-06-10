from fastapi import APIRouter
from pydantic import BaseModel
from app.core.executor import executor

router = APIRouter(prefix="/api/v1/restores", tags=["restore"])


class EtcdRestorePreflightRequest(BaseModel):
    snapshot_path: str


class VMRestoreRequest(BaseModel):
    restore_name: str
    target_namespace: str = ""
    confirm: bool = False
    confirm_phrase: str = ""


@router.post("/etcd/preflight")
def etcd_restore_preflight(req: EtcdRestorePreflightRequest):
    return executor.submit(
        "0091-etcd-restore-preflight.yml",
        {
            "backup_enabled": True,
            "etcd_restore_enabled": True,
            "etcd_restore_snapshot_path": req.snapshot_path,
        },
    )


@router.post("/vm")
def vm_restore(req: VMRestoreRequest):
    return executor.submit(
        "0096-kubevirt-vm-restore.yml",
        {
            "vm_restore_enabled": True,
            "vm_restore_apply_confirm": req.confirm,
            "vm_restore_name": req.restore_name,
            "vm_restore_target_namespace": req.target_namespace,
            "vm_restore_confirm_phrase": req.confirm_phrase,
        },
    )
