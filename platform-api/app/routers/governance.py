from fastapi import APIRouter

from app.services.executor import executor

router = APIRouter(prefix="/governance", tags=["governance"])


@router.post("/scheduling")
def scheduling_policy_check():
    return executor.run_playbook("governance.scheduling", "0074-scheduling-policy-check.yml", {"node_pools_enabled": True})


@router.post("/failure-domain")
def failure_domain_check():
    return executor.run_playbook("governance.failure_domain", "0076-failure-domain-check.yml", {"node_pools_enabled": True})


@router.post("/capacity")
def capacity_planning():
    return executor.run_playbook("governance.capacity", "0077-capacity-planning.yml")


@router.post("/admission-baseline")
def admission_baseline():
    return executor.run_playbook("governance.admission_baseline", "0078-cluster-admission-baseline.yml")
