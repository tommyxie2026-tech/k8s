from fastapi import APIRouter

from app.core.executor import executor

router = APIRouter(prefix="/storagepools", tags=["storagepools"])


@router.get("")
def list_storagepools() -> dict[str, list[str]]:
    return {"storagepools": ["local-lvm", "nfs-csi", "iscsi-san", "ceph-rbd", "ceph-rbd-retain", "cephfs"]}


@router.post("/health-check")
def health_check():
    return executor.submit("0073-storage-pool-health-check.yml", {"storage_pools_enabled": True})


@router.post("/storageclass-governance")
def storageclass_governance():
    return executor.submit("0075-storageclass-governance.yml", {"storage_pools_enabled": True})


@router.post("/volume-snapshot-check")
def volume_snapshot_check():
    return executor.submit("0094-volume-snapshot-check.yml")
