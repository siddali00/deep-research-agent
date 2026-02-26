from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def compute_fact_recall(
    expected_facts: list[dict],
    extracted_facts: list[dict],
    match_threshold: float = 0.6,
) -> dict:
    """Compute recall: what fraction of expected facts did the agent find?

    Uses substring matching with a similarity heuristic since LLM-extracted
    claims won't be verbatim matches.
    """
    matched = []
    unmatched = []

    for expected in expected_facts:
        expected_claim = expected["claim"].lower()
        found = False
        for extracted in extracted_facts:
            extracted_claim = extracted.get("claim", "").lower()
            if _fuzzy_match(expected_claim, extracted_claim, match_threshold):
                matched.append({"expected": expected["claim"], "matched_with": extracted.get("claim")})
                found = True
                break
        if not found:
            unmatched.append(expected["claim"])

    total = len(expected_facts)
    recall = len(matched) / total if total > 0 else 0.0

    return {
        "recall": round(recall, 3),
        "matched_count": len(matched),
        "total_expected": total,
        "matched": matched,
        "unmatched": unmatched,
    }


def compute_precision(extracted_facts: list[dict]) -> dict:
    """Estimate precision based on confidence scores.

    True precision requires human labeling; this is an approximation using
    the agent's own confidence signals.
    """
    if not extracted_facts:
        return {"estimated_precision": 0.0, "total_extracted": 0}

    high_conf = [f for f in extracted_facts if f.get("confidence", 0) >= 0.7]
    return {
        "estimated_precision": round(len(high_conf) / len(extracted_facts), 3),
        "total_extracted": len(extracted_facts),
        "high_confidence_count": len(high_conf),
    }


def compute_f1(recall: float, precision: float) -> float:
    if recall + precision == 0:
        return 0.0
    return round(2 * (recall * precision) / (recall + precision), 3)


def evaluate_risks(expected_risks: list[str], identified_risks: list[dict]) -> dict:
    """Evaluate how well the agent identified expected risk categories."""
    identified_descriptions = " ".join(
        r.get("description", "").lower() + " " + r.get("risk_category", "").lower()
        for r in identified_risks
    )

    matched = []
    missed = []
    for expected in expected_risks:
        keywords = expected.lower().split()
        if any(kw in identified_descriptions for kw in keywords if len(kw) > 3):
            matched.append(expected)
        else:
            missed.append(expected)

    return {
        "risk_recall": round(len(matched) / len(expected_risks), 3) if expected_risks else 0.0,
        "matched_risks": matched,
        "missed_risks": missed,
    }


def _fuzzy_match(expected: str, extracted: str, threshold: float) -> bool:
    """Simple keyword-overlap similarity."""
    if not expected or not extracted:
        return False

    expected_words = set(expected.split())
    extracted_words = set(extracted.split())

    stop_words = {"a", "an", "the", "of", "in", "at", "is", "was", "for", "and", "to", "with"}
    expected_words -= stop_words
    extracted_words -= stop_words

    if not expected_words:
        return False

    overlap = expected_words & extracted_words
    similarity = len(overlap) / len(expected_words)
    return similarity >= threshold
