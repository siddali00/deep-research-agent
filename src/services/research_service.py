from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.graphs.research_graph import build_research_graph
from src.graphs.state import ResearchState
from src.db.queries.identity_graph import IdentityGraphQueries
from src.services.scoring_service import aggregate_confidence_stats

logger = logging.getLogger(__name__)


class ResearchJob:
    def __init__(self, job_id: str, target_name: str, target_context: str):
        self.job_id = job_id
        self.target_name = target_name
        self.target_context = target_context
        self.status = "pending"
        self.created_at = datetime.now(timezone.utc)
        self.completed_at: datetime | None = None
        self.result: dict[str, Any] | None = None
        self.error: str | None = None


_jobs: dict[str, ResearchJob] = {}


class ResearchService:
    """Orchestrates LangGraph research runs and manages their lifecycle."""

    def __init__(self):
        self._graph = build_research_graph()

    def start_research(self, target_name: str, target_context: str = "") -> str:
        job_id = str(uuid.uuid4())
        job = ResearchJob(job_id, target_name, target_context)
        _jobs[job_id] = job
        logger.info("Created research job %s for target '%s'", job_id, target_name)
        return job_id

    def run_research(self, job_id: str) -> dict[str, Any]:
        """Execute the research graph synchronously."""
        job = _jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = "running"
        logger.info("Starting research execution for job %s", job_id)

        initial_state: ResearchState = {
            "target_name": job.target_name,
            "target_context": job.target_context,
            "research_plan": [],
            "search_history": [],
            "extracted_facts": [],
            "connections": [],
            "risk_flags": [],
            "confidence_scores": {},
            "iteration": 0,
            "status": "planning",
            "final_report": None,
        }

        try:
            final_state = self._graph.invoke(initial_state)
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            job.result = self._format_result(final_state)

            self._save_report(job)
            self._build_identity_graph(job, final_state)

            logger.info("Research job %s completed successfully", job_id)
            return job.result

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            logger.error("Research job %s failed: %s", job_id, e, exc_info=True)
            raise

    def get_job(self, job_id: str) -> ResearchJob | None:
        return _jobs.get(job_id)

    def get_job_status(self, job_id: str) -> dict:
        job = _jobs.get(job_id)
        if not job:
            return {"error": "Job not found"}
        return {
            "job_id": job.job_id,
            "target_name": job.target_name,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error": job.error,
        }

    def _format_result(self, state: dict) -> dict:
        stats = aggregate_confidence_stats(state.get("extracted_facts", []))
        return {
            "target_name": state.get("target_name", ""),
            "iterations": state.get("iteration", 0),
            "final_report": state.get("final_report", ""),
            "facts": state.get("extracted_facts", []),
            "risk_flags": state.get("risk_flags", []),
            "connections": state.get("connections", []),
            "confidence_stats": stats,
            "search_queries_executed": len(state.get("search_history", [])),
        }

    def _save_report(self, job: ResearchJob) -> None:
        if not job.result or not job.result.get("final_report"):
            return

        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        filename = f"{job.target_name.replace(' ', '_')}_{job.job_id[:8]}.md"
        filepath = reports_dir / filename
        filepath.write_text(job.result["final_report"], encoding="utf-8")
        logger.info("Report saved to %s", filepath)

    def _build_identity_graph(self, job: ResearchJob, state: dict) -> None:
        try:
            graph_queries = IdentityGraphQueries()
            graph_queries.build_from_research(
                target_name=job.target_name,
                facts=state.get("extracted_facts", []),
                connections=state.get("connections", []),
            )
        except Exception as e:
            logger.warning("Identity graph construction failed (Neo4j may be offline): %s", e)
