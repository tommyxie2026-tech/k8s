from fastapi import APIRouter
from pydantic import BaseModel
from app.core.executor import executor

router = APIRouter(prefix="/api/v1/backups", tags=["backup"])


class EtcdBackupRequest(BaseModel):
    confirm: bool = False


class VMBackupRequest(BaseModel):
    namespace: str = "default"
    name: str
    confirm: bool = False


@router.post("/etcd")
def etcd_backup(req: EtcdBackupRequest):
    return executor.submit(
        "0090-etcd-backup.yml",
        {
            "backup_enabled": True,
            "etcd_backup_enabled": True,
            "backup_apply_confirm": req.confirm,
        },
    )


@router.post("/velero/preflight")
def velero_preflight():
    return executor.submit("0092-velero-preflight.yml")


@router.post("/vm")
def vm_backup(req: VMBackupRequest):
    return executor.submit(
        "0095-kubevirt-vm-backup.yml",
        {
            "vm_backup_enabled": True,
            "vm_backup_apply_confirm": req.confirm,
            "vm_backup_namespace": req.namespace,
            "vm_backup_name": req.name,
        },
    )
