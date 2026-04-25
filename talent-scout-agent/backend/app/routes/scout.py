"""API routes for the Talent Scout Agent."""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models.schemas import ScoutRequest, JobStatus
from app.services.orchestrator import create_job, run_pipeline, get_job, list_jobs

router = APIRouter(prefix="/api", tags=["scout"])


@router.post("/scout", response_model=dict)
def start_scout(request: ScoutRequest, background_tasks: BackgroundTasks):
    """Kick off a scouting job. Returns a job_id to poll."""
    job_id = create_job(request)
    background_tasks.add_task(run_pipeline, job_id, request)
    return {"job_id": job_id, "status_url": f"/api/jobs/{job_id}"}


@router.get("/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    """Poll for job status. When stage=='complete', result will be populated."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs", response_model=list[JobStatus])
def list_all_jobs():
    """List recent jobs (for debugging / history)."""
    return list_jobs()


@router.get("/health")
def health():
    return {"status": "ok"}
