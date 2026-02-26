from __future__ import annotations

import logging

from src.services.research_service import ResearchService
from src.services.report_service import ReportService

logger = logging.getLogger(__name__)

_research_service = ResearchService()
_report_service = ReportService()


def get_report(job_id: str) -> str | None:
    job = _research_service.get_job(job_id)
    if not job or not job.result:
        return None
    return _report_service.get_report(job.result)


def get_summary(job_id: str) -> dict | None:
    job = _research_service.get_job(job_id)
    if not job or not job.result:
        return None
    return _report_service.get_summary(job.result)


def get_risks(job_id: str) -> list[dict] | None:
    job = _research_service.get_job(job_id)
    if not job or not job.result:
        return None
    return _report_service.get_risk_report(job.result)
