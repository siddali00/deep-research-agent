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

REPORTER_SYSTEM_PROMPT = """\
You are the Elile Research Agent — an intelligence report writer producing \
comprehensive risk assessment and due diligence reports.

You MUST follow this EXACT markdown template. Do NOT add, remove, or rename \
any section. Do NOT invent a date or title — those are added externally. \
Fill in ONLY the content inside each section.

---
## 1. Executive Summary
<2-3 paragraphs: overview of subject, most critical findings, key risks, and information gaps>

## 2. Subject Profile
| Field | Detail |
|-------|--------|
| **Full Name** | <full legal name if known> |
| **Role(s)** | <current and former titles> |
| **Location** | <city, state, country> |
| **Key Affiliations** | <companies, organizations> |
| **Registration / Licenses** | <professional registrations if any> |
| **Key Associates** | <names and relationships> |

## 3. Key Findings

### 3.1 Legal & Regulatory
- <bullet points, each ending with [confidence: X.XX]>

### 3.2 Financial
- <bullet points with [confidence: X.XX]>

### 3.3 Professional & Operational
- <bullet points with [confidence: X.XX]>

### 3.4 Network & Associations
- <bullet points with [confidence: X.XX]>

### 3.5 Reputational
- <bullet points with [confidence: X.XX]>

## 4. Risk Assessment
| Category | Severity | Description | Supporting Evidence |
|----------|----------|-------------|---------------------|
| <Legal / Financial / Operational / Network / Reputational> | <Critical / High / Medium / Low> | <description> | <fact indices or brief reference> |

## 5. Connection Map
| Source Entity | Target Entity | Relationship | Significance | Confidence |
|---------------|---------------|--------------|--------------|------------|
| <...> | <...> | <...> | <...> | <0.XX> |

## 6. Source Assessment
- **Primary sources:** <list of authoritative sources used>
- **Information gaps:** <areas where data is notably absent>
- **Limitations:** <caveats about the research>

## 7. Recommendations
1. <numbered actionable recommendations for deeper investigation>

## 8. Appendix — Sources Consulted
1. [<title>](<url>)
---

Rules:
- Use formal, objective language
- Clearly distinguish between verified facts and assessments
- Include [confidence: X.XX] for every key claim in section 3
- Highlight the most critical findings prominently
- If a section has no data, write "No findings in this category."
- Do NOT add any sections, headers, titles, or dates beyond the template above"""

REPORTER_USER_PROMPT = """\
Report date: {today_date}
Subject: {target_name}
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

Generate the report by filling in ONLY the template sections defined in the system prompt. \
Do NOT add a title, date, or any content outside the template."""


def reporter_node(state: ResearchState) -> dict:
    """Generate the final comprehensive research report."""
    logger.info("Reporter node: generating final report")

    router = ModelRouter()

    facts = _apply_scores(
        state.get("extracted_facts", []),
        state.get("confidence_scores", {}),
    )
    risks = state.get("risk_flags", [])
    connections = state.get("connections", [])
    search_history = state.get("search_history", [])

    confidences = [f.get("confidence", 0.5) for f in facts]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    high_conf = sum(1 for c in confidences if c >= 0.7)
    low_conf = sum(1 for c in confidences if c < 0.5)
    now = datetime.now(timezone.utc)

    user_prompt = REPORTER_USER_PROMPT.format(
        today_date=now.strftime("%Y-%m-%d"),
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
        high_confidence_count=high_conf,
        low_confidence_count=low_conf,
        query_count=len(search_history),
        queries=json.dumps([sh["query"] for sh in search_history], indent=2)[:2000],
    )

    messages = [
        SystemMessage(content=REPORTER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = resilient_invoke(router, TaskType.REPORTING, messages, temperature=0.3)
    if response:
        body = ensure_str(response.content)
    else:
        body = _fallback_report(facts, risks)

    header = _build_header(
        target_name=state["target_name"],
        target_context=state.get("target_context", ""),
        generated=now,
        iterations=state.get("iteration", 0),
        fact_count=len(facts),
        risk_count=len(risks),
        connection_count=len(connections),
        query_count=len(search_history),
        avg_confidence=avg_conf,
        high_confidence=high_conf,
        low_confidence=low_conf,
    )

    appendix = _build_appendix(facts, risks, connections, search_history)
    final_report = header + "\n" + body + "\n\n" + appendix

    logger.info("Report generated: %d characters", len(final_report))
    return {
        "final_report": final_report,
        "status": "done",
    }


def _apply_scores(facts: list[dict], scores: dict[str, float]) -> list[dict]:
    """Return a copy of facts with confidence_scores applied."""
    updated = []
    for f in facts:
        claim = f.get("claim", "")
        if claim in scores:
            updated.append({**f, "confidence": scores[claim]})
        else:
            updated.append(f)
    return updated


def _build_header(
    *,
    target_name: str,
    target_context: str,
    generated: datetime,
    iterations: int,
    fact_count: int,
    risk_count: int,
    connection_count: int,
    query_count: int,
    avg_confidence: float,
    high_confidence: int,
    low_confidence: int,
) -> str:
    return (
        f"# Deep Research Report: {target_name}\n\n"
        f"| Field | Value |\n"
        f"|-------|-------|\n"
        f"| **Prepared by** | Elile Research Agent |\n"
        f"| **Generated** | {generated.strftime('%Y-%m-%d %H:%M UTC')} |\n"
        f"| **Subject** | {target_name} |\n"
        f"| **Context** | {target_context or 'N/A'} |\n"
        f"| **Iterations** | {iterations} |\n"
        f"| **Facts Extracted** | {fact_count} |\n"
        f"| **Risk Flags** | {risk_count} |\n"
        f"| **Connections** | {connection_count} |\n"
        f"| **Queries Executed** | {query_count} |\n"
        f"| **Avg Confidence** | {avg_confidence:.2f} |\n"
        f"| **High Confidence (≥0.7)** | {high_confidence} |\n"
        f"| **Low Confidence (<0.5)** | {low_confidence} |\n"
    )


def _build_appendix(
    facts: list[dict],
    risks: list[dict],
    connections: list[dict],
    search_history: list[dict],
) -> str:
    """Build code-generated appendix tables from raw state data."""
    sections: list[str] = []

    # --- Appendix B: All Extracted Facts ---
    sections.append("## Appendix B — All Extracted Facts\n")
    if facts:
        sections.append("| # | Category | Claim | Source | Confidence |")
        sections.append("|---|----------|-------|--------|------------|")
        for i, f in enumerate(facts, 1):
            cat = f.get("category", "unknown")
            claim = f.get("claim", "").replace("|", "\\|")
            source = f.get("source_title", f.get("source_url", "N/A")).replace("|", "\\|")
            conf = f.get("confidence", 0.5)
            sections.append(f"| {i} | {cat} | {claim} | {source} | {conf:.2f} |")
    else:
        sections.append("No facts extracted.\n")

    sections.append("")

    # --- Appendix C: All Risk Flags ---
    sections.append("## Appendix C — All Risk Flags\n")
    if risks:
        sections.append("| # | Category | Severity | Description | Recommendations |")
        sections.append("|---|----------|----------|-------------|-----------------|")
        for i, r in enumerate(risks, 1):
            cat = r.get("risk_category", "unknown")
            sev = r.get("severity", "unknown")
            desc = r.get("description", "").replace("|", "\\|")
            recs = r.get("recommendations", "")
            if isinstance(recs, list):
                recs = "; ".join(recs)
            recs = str(recs).replace("|", "\\|")
            sections.append(f"| {i} | {cat} | {sev} | {desc} | {recs} |")
    else:
        sections.append("No risk flags identified.\n")

    sections.append("")

    # --- Appendix D: All Connections ---
    sections.append("## Appendix D — All Connections\n")
    if connections:
        sections.append("| # | Source Entity | Target Entity | Relationship | Description | Confidence |")
        sections.append("|---|-------------|---------------|--------------|-------------|------------|")
        for i, c in enumerate(connections, 1):
            src = c.get("source_entity", "").replace("|", "\\|")
            tgt = c.get("target_entity", "").replace("|", "\\|")
            rel = c.get("relationship", "").replace("|", "\\|")
            desc = c.get("description", "").replace("|", "\\|")
            conf = c.get("confidence", 0.5)
            sections.append(f"| {i} | {src} | {tgt} | {rel} | {desc} | {conf:.2f} |")
    else:
        sections.append("No connections identified.\n")

    sections.append("")

    # --- Appendix E: Search Queries ---
    sections.append("## Appendix E — Search Queries Executed\n")
    if search_history:
        sections.append("| # | Query | Results |")
        sections.append("|---|-------|---------|")
        for i, sh in enumerate(search_history, 1):
            query = sh.get("query", "").replace("|", "\\|")
            count = len(sh.get("results", []))
            sections.append(f"| {i} | {query} | {count} |")
    else:
        sections.append("No queries executed.\n")

    return "\n".join(sections)


def _fallback_report(facts: list[dict], risks: list[dict]) -> str:
    sections = [
        "---",
        "## 1. Executive Summary",
        "*Report generation failed. Raw data is presented below.*\n",
        "## 3. Key Findings\n",
    ]

    for f in facts:
        sections.append(
            f"- [{f.get('category', 'unknown')}] {f.get('claim', '')} "
            f"[confidence: {f.get('confidence', 0.5):.2f}]"
        )

    sections.append("\n## 4. Risk Assessment\n")
    sections.append("| Category | Severity | Description |")
    sections.append("|----------|----------|-------------|")
    for r in risks:
        sections.append(
            f"| {r.get('risk_category', '')} | {r.get('severity', '')} "
            f"| {r.get('description', '')} |"
        )

    return "\n".join(sections)
