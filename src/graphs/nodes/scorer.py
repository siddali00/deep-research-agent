"""Fact confidence scoring node -- runs in parallel with analyzer."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import SystemMessage, HumanMessage

from src.config.models import TaskType
from src.models.router import ModelRouter
from src.graphs.state import ResearchState
from src.utils.text import robust_json_loads
from src.utils.llm_retry import resilient_invoke
from src.utils.prompts.validation import VALIDATION_SYSTEM_PROMPT, VALIDATION_USER_PROMPT

logger = logging.getLogger(__name__)


def scorer_node(state: ResearchState) -> dict:
    """Score NEW facts with confidence values via LLM."""
    all_facts = state.get("extracted_facts", [])
    new_facts = [f for f in all_facts if f.get("confidence", 0.5) == 0.5]
    logger.info("Scorer node: %d new facts to score (of %d total)", len(new_facts), len(all_facts))

    if not new_facts:
        return {"confidence_scores": {}}

    router = ModelRouter()

    facts_json = json.dumps(
        [
            {"index": i, "claim": f["claim"], "source_url": f.get("source_url", ""),
             "source_title": f.get("source_title", ""), "category": f.get("category", "")}
            for i, f in enumerate(new_facts)
        ],
        indent=2,
    )

    history_summary = json.dumps(
        [{"query": sh["query"], "result_count": len(sh.get("results", []))}
         for sh in state.get("search_history", [])[-10:]],
        indent=2,
    )

    user_prompt = VALIDATION_USER_PROMPT.format(
        target_name=state["target_name"],
        facts_to_validate=facts_json,
        search_history=history_summary,
    )

    messages = [
        SystemMessage(content=VALIDATION_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = resilient_invoke(router, TaskType.VALIDATION, messages, temperature=0.0, json_mode=True)
    if not response:
        return {"confidence_scores": {}}

    parsed = robust_json_loads(response.content, context="scorer._score_facts")
    scores = parsed if isinstance(parsed, list) else []
    result = {}
    for score_entry in scores:
        if not isinstance(score_entry, dict):
            continue
        idx = score_entry.get("fact_index", -1)
        if 0 <= idx < len(new_facts):
            result[new_facts[idx]["claim"]] = score_entry.get("confidence", 0.5)

    logger.info("Scored %d facts", len(result))
    return {"confidence_scores": result}
