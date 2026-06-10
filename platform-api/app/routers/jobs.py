from fastapi import APIRouter, HTTPException

from app.services.executor import executor

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
def list_jobs():
    return executor.list_jobs()


@router.get("/{job_id}")
def get_job(job_id: str):
    job = executor.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job
