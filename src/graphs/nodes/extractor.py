from __future__ import annotations

import json
import logging

from langchain_core.messages import SystemMessage, HumanMessage

from src.config.models import TaskType
from src.models.router import ModelRouter
from src.graphs.state import ResearchState
from src.utils.text import robust_json_loads
from src.utils.llm_retry import resilient_invoke
from src.utils.prompts.extraction import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_USER_PROMPT,
)

logger = logging.getLogger(__name__)


def extractor_node(state: ResearchState) -> dict:
    """Extract structured facts from this iteration's search results in a single batched LLM call."""
    logger.info("Extractor node: processing search results")

    router = ModelRouter()

    search_history = state.get("search_history", [])
    existing_facts = state.get("extracted_facts", [])
    existing_claims = {f.get("claim", "") for f in existing_facts}
    plan_queries = set(state.get("research_plan", []))

    existing_facts_summary = json.dumps(
        [{"claim": f["claim"], "category": f["category"]} for f in existing_facts[:50]],
        indent=2,
    ) if existing_facts else "[]"

    new_searches = [
        s for s in search_history
        if s["query"] in plan_queries and s.get("results")
    ]

    if not new_searches:
        logger.info("No new search results to extract from")
        return {"extracted_facts": [], "status": "analyzing"}

    all_results_text = _format_all_results(new_searches)

    user_prompt = EXTRACTION_USER_PROMPT.format(
        target_name=state["target_name"],
        search_results=all_results_text,
        existing_facts=existing_facts_summary,
    )

    messages = [
        SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    new_facts = []
    response = resilient_invoke(router, TaskType.EXTRACTION, messages, temperature=0.0, json_mode=True)
    if response:
        facts = _parse_facts(response.content)
        for fact in facts:
            if fact.get("claim") and fact["claim"] not in existing_claims:
                fact.setdefault("confidence", 0.5)
                new_facts.append(fact)
                existing_claims.add(fact["claim"])

    logger.info("Extracted %d new facts from %d searches (single LLM call)", len(new_facts), len(new_searches))
    return {
        "extracted_facts": new_facts,
        "status": "analyzing",
    }


def _format_all_results(searches: list[dict]) -> str:
    """Format all search results from multiple queries into a single text block."""
    sections = []
    for search_entry in searches:
        query = search_entry["query"]
        results = search_entry.get("results", [])
        section = f"=== Query: {query} ===\n"
        for r in results:
            section += (
                f"Title: {r.get('title', 'N/A')}\n"
                f"URL: {r.get('url', 'N/A')}\n"
                f"Content: {r.get('content', 'N/A')}\n---\n"
            )
        sections.append(section)
    return "\n".join(sections)


def _parse_facts(content) -> list[dict]:
    parsed = robust_json_loads(content, context="extractor._parse_facts")
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for val in parsed.values():
            if isinstance(val, list):
                return val
    return []
