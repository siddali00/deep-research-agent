from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from src.services.research_service import ResearchService

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)
_research_service = ResearchService()


def start_research(target_name: str, target_context: str = "") -> dict:
    job_id = _research_service.start_research(target_name, target_context)
    _executor.submit(_run_research_background, job_id)
    return {
        "job_id": job_id,
        "target_name": target_name,
        "status": "started",
        "message": f"Research started for '{target_name}'. Poll /api/research/{job_id}/status for updates.",
    }


def get_status(job_id: str) -> dict:
    return _research_service.get_job_status(job_id)


def get_result(job_id: str) -> dict | None:
    job = _research_service.get_job(job_id)
    if not job or not job.result:
        return None
    r = job.result
    stats = r.get("confidence_stats", {})
    return {
        "target_name": r["target_name"],
        "iterations": r["iterations"],
        "total_facts": stats.get("total_facts", 0),
        "total_risks": len(r.get("risk_flags", [])),
        "avg_confidence": stats.get("avg_confidence", 0.0),
        "connections_count": len(r.get("connections", [])),
        "queries_executed": r.get("search_queries_executed", 0),
        "final_report": r.get("final_report", ""),
    }


def _run_research_background(job_id: str) -> None:
    try:
        _research_service.run_research(job_id)
    except Exception as e:
        logger.error("Background research failed for %s: %s", job_id, e)
