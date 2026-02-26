from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    target_name: str = Field(..., min_length=1, description="Full name of the research target")
    target_context: str = Field(
        default="",
        description="Additional context (role, company, etc.)",
    )


class ResearchResponse(BaseModel):
    job_id: str
    target_name: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    target_name: str
    status: str
    created_at: str
    completed_at: str | None = None
    error: str | None = None


class ResearchResultResponse(BaseModel):
    target_name: str
    iterations: int
    total_facts: int
    total_risks: int
    avg_confidence: float
    connections_count: int
    queries_executed: int
    final_report: str
