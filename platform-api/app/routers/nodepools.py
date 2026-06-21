from fastapi import APIRouter

from app.core.executor import executor

router = APIRouter(prefix="/nodepools", tags=["nodepools"])


@router.get("")
def list_nodepools() -> dict[str, list[str]]:
    return {"nodepools": ["control-plane", "compute", "vm", "storage", "gpu", "edge"]}


@router.post("/health-check")
def health_check():
    return executor.submit("0072-node-pool-health-check.yml", {"node_pools_enabled": True})


@router.post("/apply-labels")
def apply_labels(confirm: bool = False):
    return executor.submit("0071-node-pool-labels.yml", {"node_pools_enabled": True, "node_pools_apply_confirm": confirm})
