from fastapi import APIRouter

from app.services.executor import executor

router = APIRouter(prefix="/observability", tags=["observability"])


@router.post("/preflight")
def observability_preflight():
    return executor.run_playbook("observability.preflight", "0080-observability-preflight.yml", {"observability_enabled": True})
