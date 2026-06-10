from fastapi import APIRouter, HTTPException
from app.core.task_store import task_store

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get("")
def list_tasks():
    return task_store.list()


@router.get("/{task_id}")
def get_task(task_id: str):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task
