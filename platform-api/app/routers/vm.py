from fastapi import APIRouter
from pydantic import BaseModel
from app.core.executor import executor

router = APIRouter(prefix="/api/v1/vms", tags=["vm"])


class VMActionRequest(BaseModel):
    namespace: str = "default"
    name: str


@router.post("/status")
def vm_status(req: VMActionRequest):
    return executor.submit(
        "0070-kubevirt-vm-ops.yml",
        {
            "kubevirt_enabled": True,
            "kubevirt_vm_action": "status",
            "kubevirt_vm_namespace": req.namespace,
            "kubevirt_vm_name": req.name,
        },
    )


@router.post("/start")
def vm_start(req: VMActionRequest):
    return executor.submit(
        "0070-kubevirt-vm-ops.yml",
        {
            "kubevirt_enabled": True,
            "kubevirt_vm_action": "start",
            "kubevirt_vm_namespace": req.namespace,
            "kubevirt_vm_name": req.name,
        },
    )


@router.post("/stop")
def vm_stop(req: VMActionRequest):
    return executor.submit(
        "0070-kubevirt-vm-ops.yml",
        {
            "kubevirt_enabled": True,
            "kubevirt_vm_action": "stop",
            "kubevirt_vm_namespace": req.namespace,
            "kubevirt_vm_name": req.name,
        },
    )
