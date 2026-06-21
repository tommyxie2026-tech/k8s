from fastapi import APIRouter

from app.core.executor import executor

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("/current")
def current_cluster() -> dict[str, str]:
    return {"name": "current", "mode": "ansible-managed"}


@router.post("/syntax-check")
def syntax_check():
    return executor.submit("0000-preflight.yml")


@router.post("/preflight")
def preflight():
    return executor.submit("0000-preflight.yml")
