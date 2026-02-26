from fastapi import APIRouter, HTTPException

from src.api.schemas.research import (
    ResearchRequest,
    ResearchResponse,
    JobStatusResponse,
    ResearchResultResponse,
)
from src.api.controllers import research as ctrl

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("/", response_model=ResearchResponse)
def create_research(request: ResearchRequest):
    result = ctrl.start_research(request.target_name, request.target_context)
    return ResearchResponse(**result)


@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_research_status(job_id: str):
    status = ctrl.get_status(job_id)
    if "error" in status and status["error"] == "Job not found":
        raise HTTPException(status_code=404, detail="Research job not found")
    return JobStatusResponse(**status)


@router.get("/{job_id}/result", response_model=ResearchResultResponse)
def get_research_result(job_id: str):
    result = ctrl.get_result(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not available yet")
    return ResearchResultResponse(**result)
