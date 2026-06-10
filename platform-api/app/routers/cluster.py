from fastapi import APIRouter
from app.core.executor import executor

router = APIRouter(prefix="/api/v1/clusters", tags=["cluster"])


@router.get("")
def list_clusters():
    return [{"name": "default", "inventory": "configured"}]


@router.post("/health")
def cluster_health():
    return executor.submit("0061-storage-health-check.yml")


@router.post("/capacity")
def cluster_capacity():
    return executor.submit("0077-capacity-planning.yml")
