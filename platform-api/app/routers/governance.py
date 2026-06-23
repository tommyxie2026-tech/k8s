from fastapi import APIRouter

from app.core.executor import executor

router = APIRouter(prefix="/governance", tags=["governance"])


@router.post("/scheduling")
def scheduling_policy_check():
    return executor.submit("0074-scheduling-policy-check.yml", {"node_pools_enabled": True})


@router.post("/failure-domain")
def failure_domain_check():
    return executor.submit("0076-failure-domain-check.yml", {"node_pools_enabled": True})


@router.post("/capacity")
def capacity_planning():
    return executor.submit("0077-capacity-planning.yml")


@router.post("/admission-baseline")
def admission_baseline():
    return executor.submit("0078-cluster-admission-baseline.yml")
