from fastapi import APIRouter
from app.core.executor import executor
from app.schemas.common import ConfirmRequest

router = APIRouter(prefix="/api/v1/nodepools", tags=["nodepool"])


@router.post("/health")
def nodepool_health():
    return executor.submit("0072-node-pool-health-check.yml", {"node_pools_enabled": True})


@router.post("/apply")
def nodepool_apply(req: ConfirmRequest):
    return executor.submit(
        "0071-node-pool-labels.yml",
        {
            "node_pools_enabled": True,
            "node_pools_apply_confirm": req.confirm,
        },
    )
