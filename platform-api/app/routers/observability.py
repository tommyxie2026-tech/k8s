from fastapi import APIRouter
from app.core.executor import executor

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])


@router.post("/preflight")
def observability_preflight():
    return executor.submit("0080-observability-preflight.yml", {"observability_enabled": True})
