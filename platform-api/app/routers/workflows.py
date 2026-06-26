from fastapi import APIRouter, HTTPException

from app.schemas.workflows import WorkflowCreateRequest
from app.services.workflow import workflow_engine

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("")
def create_workflow(request: WorkflowCreateRequest):
    try:
        return workflow_engine.create(request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("")
def list_workflows():
    return workflow_engine.list()


@router.get("/{workflow_id}")
def get_workflow(workflow_id: str):
    workflow = workflow_engine.get(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="workflow not found")
    return workflow
