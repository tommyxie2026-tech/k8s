from fastapi import APIRouter
from pydantic import BaseModel

from app.core.executor import executor

router = APIRouter(prefix="/backups", tags=["backup"])


class EtcdBackupRequest(BaseModel):
    confirm: bool = False


class EtcdRestorePreflightRequest(BaseModel):
    snapshot_path: str


class VeleroInstallRequest(BaseModel):
    confirm: bool = False


class VMBackupRequest(BaseModel):
    namespace: str = "default"
    name: str
    confirm: bool = False


class VMRestoreRequest(BaseModel):
    name: str
    target_namespace: str = ""
    confirm: bool = False
    confirm_phrase: str = ""


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


@router.post("/etcd/restore-preflight")
def etcd_restore_preflight(req: EtcdRestorePreflightRequest):
    return executor.submit(
        "0091-etcd-restore-preflight.yml",
        {
            "backup_enabled": True,
            "etcd_restore_enabled": True,
            "etcd_restore_snapshot_path": req.snapshot_path,
        },
    )


@router.post("/velero/preflight")
def velero_preflight():
    return executor.submit("0092-velero-preflight.yml")


@router.post("/velero/install-plan")
def velero_install_plan(req: VeleroInstallRequest):
    return executor.submit("0093-install-velero.yml", {"velero_enabled": True, "velero_install_confirm": req.confirm})


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


@router.post("/vm/restore")
def vm_restore(req: VMRestoreRequest):
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
