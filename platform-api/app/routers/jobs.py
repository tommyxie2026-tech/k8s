from fastapi import APIRouter, HTTPException

from app.core.task_store import task_store

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
def list_jobs():
    return task_store.list()


@router.get("/{task_id}")
def get_job(task_id: str):
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task
