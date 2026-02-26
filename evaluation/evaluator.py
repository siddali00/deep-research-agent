from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.services.research_service import ResearchService
from evaluation.metrics import (
    compute_fact_recall,
    compute_precision,
    compute_f1,
    evaluate_risks,
)

logger = logging.getLogger(__name__)


class Evaluator:
    """Runs the research agent against test personas and scores performance."""

    def __init__(self):
        self._service = ResearchService()
        self._personas_dir = Path("evaluation/personas")

    def load_persona(self, filename: str) -> dict:
        filepath = self._personas_dir / filename
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)

    def evaluate_persona(self, persona: dict) -> dict:
        """Run the agent on a persona and evaluate results."""
        name = persona["name"]
        context = persona.get("context", "")

        logger.info("Starting evaluation for persona: %s", name)

        job_id = self._service.start_research(name, context)
        result = self._service.run_research(job_id)

        extracted_facts = result.get("facts", [])
        identified_risks = result.get("risk_flags", [])

        fact_recall = compute_fact_recall(persona["expected_facts"], extracted_facts)
        precision = compute_precision(extracted_facts)
        f1 = compute_f1(fact_recall["recall"], precision["estimated_precision"])
        risk_eval = evaluate_risks(persona.get("expected_risks", []), identified_risks)

        evaluation = {
            "persona": name,
            "difficulty": persona.get("difficulty", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "fact_recall": fact_recall,
                "precision": precision,
                "f1_score": f1,
                "risk_evaluation": risk_eval,
            },
            "stats": result.get("confidence_stats", {}),
            "iterations": result.get("iterations", 0),
            "queries_executed": result.get("search_queries_executed", 0),
        }

        logger.info(
            "Evaluation for %s: recall=%.3f, precision=%.3f, F1=%.3f",
            name, fact_recall["recall"], precision["estimated_precision"], f1,
        )

        return evaluation

    def run_all(self) -> list[dict]:
        """Evaluate all personas and save results."""
        results = []
        for persona_file in sorted(self._personas_dir.glob("persona_*.json")):
            persona = self.load_persona(persona_file.name)
            evaluation = self.evaluate_persona(persona)
            results.append(evaluation)

        self._save_results(results)
        return results

    def _save_results(self, results: list[dict]) -> None:
        out_dir = Path("reports")
        out_dir.mkdir(exist_ok=True)
        filepath = out_dir / "evaluation_results.json"
        filepath.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
        logger.info("Evaluation results saved to %s", filepath)


if __name__ == "__main__":
    from src.utils.logging import setup_logging
    setup_logging()
    evaluator = Evaluator()
    evaluator.run_all()
