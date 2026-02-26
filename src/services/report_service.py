from __future__ import annotations

import json
import logging
from pathlib import Path

from src.services.scoring_service import aggregate_confidence_stats

logger = logging.getLogger(__name__)


class ReportService:
    """Formats and manages research reports."""

    def get_report(self, job_result: dict) -> str:
        """Return the full markdown report."""
        return job_result.get("final_report", "No report generated.")

    def get_summary(self, job_result: dict) -> dict:
        """Return a structured summary of the research."""
        stats = job_result.get("confidence_stats", {})
        risks = job_result.get("risk_flags", [])

        critical_risks = [r for r in risks if r.get("severity") == "critical"]
        high_risks = [r for r in risks if r.get("severity") == "high"]

        return {
            "target": job_result.get("target_name", ""),
            "iterations": job_result.get("iterations", 0),
            "total_facts": stats.get("total_facts", 0),
            "avg_confidence": stats.get("avg_confidence", 0.0),
            "total_risks": len(risks),
            "critical_risks": len(critical_risks),
            "high_risks": len(high_risks),
            "connections": len(job_result.get("connections", [])),
            "queries_executed": job_result.get("search_queries_executed", 0),
        }

    def get_risk_report(self, job_result: dict) -> list[dict]:
        """Return risks sorted by severity."""
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        risks = job_result.get("risk_flags", [])
        return sorted(risks, key=lambda r: severity_order.get(r.get("severity", "low"), 4))

    def export_report(self, job_result: dict, output_dir: str = "reports") -> str:
        """Export the full report to disk."""
        target = job_result.get("target_name", "unknown").replace(" ", "_")
        out = Path(output_dir)
        out.mkdir(exist_ok=True)

        md_path = out / f"{target}_report.md"
        md_path.write_text(
            job_result.get("final_report", "No report."), encoding="utf-8"
        )

        json_path = out / f"{target}_data.json"
        export_data = {
            "target": job_result.get("target_name"),
            "facts": job_result.get("facts", []),
            "risk_flags": job_result.get("risk_flags", []),
            "connections": job_result.get("connections", []),
            "confidence_stats": job_result.get("confidence_stats", {}),
        }
        json_path.write_text(json.dumps(export_data, indent=2, default=str), encoding="utf-8")

        logger.info("Reports exported to %s", out)
        return str(out)
