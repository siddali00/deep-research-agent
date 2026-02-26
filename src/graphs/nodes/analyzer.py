from __future__ import annotations

import json
import logging

from langchain_core.messages import SystemMessage, HumanMessage

from src.config.models import TaskType
from src.models.router import ModelRouter
from src.graphs.state import ResearchState
from src.utils.text import robust_json_loads
from src.utils.llm_retry import resilient_invoke
from src.utils.prompts.analysis import ANALYSIS_SYSTEM_PROMPT, ANALYSIS_USER_PROMPT

logger = logging.getLogger(__name__)


def analyzer_node(state: ResearchState) -> dict:
    """Analyze accumulated facts for risk patterns, connections, and inconsistencies."""
    logger.info("Analyzer node: analyzing %d facts", len(state.get("extracted_facts", [])))

    router = ModelRouter()

    facts = state.get("extracted_facts", [])
    existing_risks = state.get("risk_flags", [])

    facts_json = json.dumps(
        [
            {
                "index": i,
                "category": f.get("category", ""),
                "claim": f.get("claim", ""),
                "source_url": f.get("source_url", ""),
                "entities": f.get("entities", []),
                "confidence": f.get("confidence", 0.5),
            }
            for i, f in enumerate(facts)
        ],
        indent=2,
    )

    existing_risks_json = json.dumps(
        [{"category": r["risk_category"], "description": r["description"]} for r in existing_risks],
        indent=2,
    ) if existing_risks else "[]"

    user_prompt = ANALYSIS_USER_PROMPT.format(
        target_name=state["target_name"],
        target_context=state.get("target_context", ""),
        fact_count=len(facts),
        extracted_facts=facts_json,
        existing_risks=existing_risks_json,
    )

    messages = [
        SystemMessage(content=ANALYSIS_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = resilient_invoke(router, TaskType.ANALYSIS, messages, temperature=0.1, json_mode=True)
    if response:
        analysis = _parse_analysis(response.content)
    else:
        analysis = {"risk_flags": [], "connections": [], "inconsistencies": [], "information_gaps": []}

    new_risks = analysis.get("risk_flags", [])
    new_connections = _build_connections(analysis.get("connections", []))

    logger.info("Identified %d new risks, %d connections", len(new_risks), len(new_connections))

    return {
        "risk_flags": new_risks,
        "connections": new_connections,
        "status": "validating",
    }


def _parse_analysis(content) -> dict:
    parsed = robust_json_loads(content, context="analyzer._parse_analysis")
    if isinstance(parsed, dict):
        return parsed
    logger.warning("Analysis returned non-dict, returning empty")
    return {}


def _build_connections(raw_connections: list) -> list[dict]:
    connections = []
    for c in raw_connections:
        if isinstance(c, dict):
            connections.append({
                "source_entity": c.get("source_entity", c.get("from", "")),
                "target_entity": c.get("target_entity", c.get("to", "")),
                "relationship": c.get("relationship", c.get("type", "ASSOCIATED_WITH")),
                "description": c.get("description", ""),
                "confidence": c.get("confidence", 0.5),
            })
    return connections
