from fastapi import APIRouter
from app.core.executor import executor

router = APIRouter(prefix="/api/v1/storagepools", tags=["storagepool"])


@router.post("/health")
def storagepool_health():
    return executor.submit("0073-storage-pool-health-check.yml", {"storage_pools_enabled": True})


@router.post("/governance")
def storageclass_governance():
    return executor.submit("0075-storageclass-governance.yml", {"storage_pools_enabled": True})


@router.post("/snapshots/check")
def volume_snapshot_check():
    return executor.submit("0094-volume-snapshot-check.yml")
