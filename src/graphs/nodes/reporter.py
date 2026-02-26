from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from langchain_core.messages import SystemMessage, HumanMessage

from src.config.models import TaskType
from src.models.router import ModelRouter
from src.graphs.state import ResearchState
from src.utils.text import ensure_str
from src.utils.llm_retry import resilient_invoke

logger = logging.getLogger(__name__)

REPORTER_SYSTEM_PROMPT = """You are an intelligence report writer producing comprehensive risk \
assessment and due diligence reports. Your reports are professional, structured, and actionable.

Report structure:
1. Executive Summary
2. Subject Profile (verified biographical and professional details)
3. Key Findings (organized by category)
4. Risk Assessment (with severity ratings)
5. Connection Map (key relationships and their significance)
6. Source Assessment (confidence overview)
7. Recommendations (next steps for deeper investigation)
8. Appendix (list of all sources consulted)

Rules:
- Use formal, objective language
- Clearly distinguish between verified facts and assessments
- Include confidence levels for key claims
- Highlight the most critical findings prominently
- Note any significant information gaps"""

REPORTER_USER_PROMPT = """Subject: {target_name}
Context: {target_context}

Research iterations completed: {iterations}

Verified Facts ({fact_count}):
{facts}

Risk Flags ({risk_count}):
{risks}

Key Connections ({connection_count}):
{connections}

Confidence Overview:
- Average confidence: {avg_confidence}
- Facts above 0.7 confidence: {high_confidence_count}
- Facts below 0.5 confidence: {low_confidence_count}

Search Queries Executed ({query_count}):
{queries}

Generate a comprehensive risk assessment report for this subject."""


def reporter_node(state: ResearchState) -> dict:
    """Generate the final comprehensive research report."""
    logger.info("Reporter node: generating final report")

    router = ModelRouter()

    facts = state.get("extracted_facts", [])
    risks = state.get("risk_flags", [])
    connections = state.get("connections", [])
    search_history = state.get("search_history", [])

    confidences = [f.get("confidence", 0.5) for f in facts]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    user_prompt = REPORTER_USER_PROMPT.format(
        target_name=state["target_name"],
        target_context=state.get("target_context", ""),
        iterations=state.get("iteration", 0),
        fact_count=len(facts),
        facts=json.dumps(facts, indent=2, default=str)[:8000],
        risk_count=len(risks),
        risks=json.dumps(risks, indent=2, default=str)[:4000],
        connection_count=len(connections),
        connections=json.dumps(connections, indent=2, default=str)[:3000],
        avg_confidence=f"{avg_conf:.2f}",
        high_confidence_count=sum(1 for c in confidences if c >= 0.7),
        low_confidence_count=sum(1 for c in confidences if c < 0.5),
        query_count=len(search_history),
        queries=json.dumps([sh["query"] for sh in search_history], indent=2)[:2000],
    )

    messages = [
        SystemMessage(content=REPORTER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = resilient_invoke(router, TaskType.REPORTING, messages, temperature=0.3)
    if response:
        report = ensure_str(response.content)
    else:
        report = _fallback_report(state)

    report_header = (
        f"# Deep Research Report: {state['target_name']}\n"
        f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
        f"Iterations: {state.get('iteration', 0)} | "
        f"Facts: {len(facts)} | Risks: {len(risks)} | "
        f"Avg Confidence: {avg_conf:.2f}\n\n"
    )

    final_report = report_header + report

    logger.info("Report generated: %d characters", len(final_report))
    return {
        "final_report": final_report,
        "status": "done",
    }


def _fallback_report(state: ResearchState) -> str:
    facts = state.get("extracted_facts", [])
    risks = state.get("risk_flags", [])

    sections = ["## Fallback Report (LLM generation failed)\n"]

    sections.append("### Facts Discovered\n")
    for f in facts:
        sections.append(f"- [{f.get('category', '')}] {f.get('claim', '')} "
                       f"(confidence: {f.get('confidence', 'N/A')})")

    sections.append("\n### Risk Flags\n")
    for r in risks:
        sections.append(f"- [{r.get('severity', '')}] {r.get('risk_category', '')}: "
                       f"{r.get('description', '')}")

    return "\n".join(sections)
