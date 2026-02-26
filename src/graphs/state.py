from __future__ import annotations

import operator
from typing import Annotated, TypedDict


def _merge_lists(left: list, right: list) -> list:
    """Reducer that appends new items to the existing list."""
    return left + right


def _merge_dicts(left: dict, right: dict) -> dict:
    """Reducer that merges dicts, with right taking precedence."""
    return {**left, **right}


class SearchResult(TypedDict):
    query: str
    results: list[dict]


class ExtractedFact(TypedDict):
    category: str
    claim: str
    source_url: str
    source_title: str
    date_mentioned: str | None
    entities: list[str]
    confidence: float


class RiskFlag(TypedDict):
    risk_category: str
    severity: str
    description: str
    supporting_facts: list[int]
    recommendations: list[str]


class Connection(TypedDict):
    source_entity: str
    target_entity: str
    relationship: str
    description: str
    confidence: float


class ResearchState(TypedDict):
    target_name: str
    target_context: str

    research_plan: list[str]
    search_history: Annotated[list[SearchResult], _merge_lists]
    extracted_facts: Annotated[list[ExtractedFact], _merge_lists]
    connections: Annotated[list[Connection], _merge_lists]
    risk_flags: Annotated[list[RiskFlag], _merge_lists]
    confidence_scores: Annotated[dict[str, float], _merge_dicts]

    iteration: int
    status: str
    final_report: str | None
