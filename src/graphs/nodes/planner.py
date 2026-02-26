from __future__ import annotations

import json
import logging

from langchain_core.messages import SystemMessage, HumanMessage

from src.config.models import TaskType
from src.models.router import ModelRouter
from src.graphs.state import ResearchState
from src.utils.text import robust_json_loads, ensure_str
from src.utils.llm_retry import resilient_invoke
from src.utils.prompts.planner import (
    PLANNER_SYSTEM_PROMPT,
    PLANNER_USER_PROMPT,
    INITIAL_PLANNER_USER_PROMPT,
)

logger = logging.getLogger(__name__)


def planner_node(state: ResearchState) -> dict:
    """Generate or refine search queries based on current research state."""
    logger.info("Planner node: iteration %d", state.get("iteration", 0))

    router = ModelRouter()

    iteration = state.get("iteration", 0)

    if iteration == 0:
        user_prompt = INITIAL_PLANNER_USER_PROMPT.format(
            target_name=state["target_name"],
            target_context=state.get("target_context", ""),
        )
    else:
        facts_summary = _summarize_facts(state.get("extracted_facts", []))
        entities = _extract_entities(state.get("extracted_facts", []))
        history = [sh["query"] for sh in state.get("search_history", [])]

        user_prompt = PLANNER_USER_PROMPT.format(
            target_name=state["target_name"],
            target_context=state.get("target_context", ""),
            iteration=iteration,
            search_history=json.dumps(history, indent=2),
            extracted_facts=facts_summary,
            discovered_entities=json.dumps(entities),
        )

    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = resilient_invoke(router, TaskType.PLANNING, messages, temperature=0.2, json_mode=True)
    queries = _parse_queries(response.content) if response else []
    logger.info("Planner generated %d queries", len(queries))

    return {
        "research_plan": queries,
        "status": "searching",
    }


def _parse_queries(content) -> list[str]:
    parsed = robust_json_loads(content, context="planner._parse_queries")
    if isinstance(parsed, list):
        return [str(q) for q in parsed if q]
    if isinstance(parsed, dict):
        for val in parsed.values():
            if isinstance(val, list):
                return [str(q) for q in val if q]
    text = ensure_str(content)
    return [line.strip().strip('"').strip("- ") for line in text.split("\n") if line.strip()]


def _summarize_facts(facts: list[dict]) -> str:
    if not facts:
        return "None yet."
    lines = []
    for i, f in enumerate(facts[:30]):
        lines.append(f"[{i}] ({f.get('category', 'unknown')}): {f.get('claim', '')}")
    return "\n".join(lines)


def _extract_entities(facts: list[dict]) -> list[str]:
    entities: set[str] = set()
    for f in facts:
        for e in f.get("entities", []):
            entities.add(e)
    return sorted(entities)[:50]
