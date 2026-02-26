from __future__ import annotations

import logging
from collections import Counter

logger = logging.getLogger(__name__)

SOURCE_CREDIBILITY_TIERS = {
    1: ["sec.gov", "courtlistener.com", "pacer.gov", "edgar", "opencorporates"],
    2: ["reuters.com", "bloomberg.com", "nytimes.com", "wsj.com", "ft.com"],
    3: ["techcrunch.com", "crunchbase.com", "pitchbook.com", "cbinsights.com"],
    4: ["linkedin.com", "news.google.com", "bbc.com", "cnn.com", "apnews.com"],
    5: ["medium.com", "reddit.com", "twitter.com", "facebook.com", "quora.com"],
}


def get_source_tier(url: str) -> int:
    if not url:
        return 5
    url_lower = url.lower()
    for tier, domains in SOURCE_CREDIBILITY_TIERS.items():
        for domain in domains:
            if domain in url_lower:
                return tier
    return 4


def compute_confidence(
    source_urls: list[str],
    corroboration_count: int = 1,
    recency_weight: float = 1.0,
) -> float:
    """Compute a confidence score for a fact based on source quality and corroboration."""
    if not source_urls:
        return 0.3

    tiers = [get_source_tier(url) for url in source_urls]
    best_tier = min(tiers) if tiers else 5

    tier_scores = {1: 0.95, 2: 0.85, 3: 0.7, 4: 0.55, 5: 0.35}
    base_score = tier_scores.get(best_tier, 0.4)

    corroboration_bonus = min(0.15, (corroboration_count - 1) * 0.05)

    score = (base_score + corroboration_bonus) * recency_weight
    return round(min(1.0, max(0.0, score)), 2)


def aggregate_confidence_stats(facts: list[dict]) -> dict:
    """Produce summary confidence statistics for a set of facts."""
    if not facts:
        return {
            "total_facts": 0,
            "avg_confidence": 0.0,
            "high_confidence_count": 0,
            "medium_confidence_count": 0,
            "low_confidence_count": 0,
            "category_breakdown": {},
        }

    confidences = [f.get("confidence", 0.5) for f in facts]
    categories = Counter(f.get("category", "unknown") for f in facts)

    return {
        "total_facts": len(facts),
        "avg_confidence": round(sum(confidences) / len(confidences), 3),
        "high_confidence_count": sum(1 for c in confidences if c >= 0.7),
        "medium_confidence_count": sum(1 for c in confidences if 0.5 <= c < 0.7),
        "low_confidence_count": sum(1 for c in confidences if c < 0.5),
        "category_breakdown": dict(categories),
    }
