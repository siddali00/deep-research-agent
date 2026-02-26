from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from src.api.schemas.reports import ReportSummaryResponse, RiskFlagResponse
from src.api.controllers import reports as ctrl

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{job_id}", response_class=PlainTextResponse)
def get_full_report(job_id: str):
    report = ctrl.get_report(job_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not available")
    return report


@router.get("/{job_id}/summary", response_model=ReportSummaryResponse)
def get_report_summary(job_id: str):
    summary = ctrl.get_summary(job_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Report not available")
    return ReportSummaryResponse(**summary)


@router.get("/{job_id}/risks", response_model=list[RiskFlagResponse])
def get_risk_flags(job_id: str):
    risks = ctrl.get_risks(job_id)
    if risks is None:
        raise HTTPException(status_code=404, detail="Report not available")
    return [RiskFlagResponse(**r) for r in risks]
