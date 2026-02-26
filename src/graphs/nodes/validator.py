"""Sufficiency check node -- decides whether to continue or report.

Runs after both analyzer and scorer complete (fan-in).
Applies scored confidence to facts, then checks if research is sufficient.
"""

from __future__ import annotations

import json
import logging

from src.config.models import TaskType
from src.config.settings import get_settings
from src.models.router import ModelRouter
from src.graphs.state import ResearchState
from src.utils.text import robust_json_loads
from src.utils.llm_retry import resilient_invoke
from src.utils.prompts.validation import SUFFICIENCY_CHECK_PROMPT

logger = logging.getLogger(__name__)


def validator_node(state: ResearchState) -> dict:
    """Apply scored confidence and decide whether to continue or report."""
    all_facts = state.get("extracted_facts", [])
    scores = state.get("confidence_scores", {})
    logger.info("Sufficiency check: %d facts, %d scores available", len(all_facts), len(scores))

    for fact in all_facts:
        claim = fact.get("claim", "")
        if claim in scores:
            fact["confidence"] = scores[claim]

    router = ModelRouter()
    settings = get_settings()
    should_continue = _check_sufficiency(router, state, settings)

    new_iteration = state.get("iteration", 0) + 1
    if should_continue and new_iteration < settings.max_research_iterations:
        next_status = "planning"
    else:
        next_status = "reporting"

    logger.info(
        "Sufficiency complete. Continue=%s, next_status=%s, iteration=%d",
        should_continue, next_status, new_iteration,
    )

    return {
        "iteration": new_iteration,
        "status": next_status,
    }


def _check_sufficiency(router: ModelRouter, state: ResearchState, settings) -> bool:
    facts = state.get("extracted_facts", [])
    risks = state.get("risk_flags", [])

    categories = {}
    for f in facts:
        cat = f.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    confidences = [f.get("confidence", 0.5) for f in facts]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    prompt = SUFFICIENCY_CHECK_PROMPT.format(
        target_name=state["target_name"],
        iteration=state.get("iteration", 0),
        max_iterations=settings.max_research_iterations,
        fact_count=len(facts),
        risk_count=len(risks),
        avg_confidence=f"{avg_confidence:.2f}",
        category_coverage=json.dumps(categories, indent=2),
        information_gaps="See analysis output",
        confidence_threshold=settings.confidence_threshold,
    )

    response = resilient_invoke(router, TaskType.VALIDATION, prompt, temperature=0.0, json_mode=True)
    if response:
        result = robust_json_loads(response.content, context="validator._check_sufficiency")
        if isinstance(result, dict):
            return result.get("continue", False)
    return state.get("iteration", 0) < 2
