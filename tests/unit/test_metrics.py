import pytest

from evaluation.metrics import (
    compute_fact_recall,
    compute_precision,
    compute_f1,
    evaluate_risks,
    _fuzzy_match,
)


class TestFuzzyMatch:
    def test_exact_match(self):
        assert _fuzzy_match("CEO of Tesla", "CEO of Tesla", 0.6)

    def test_partial_match(self):
        assert _fuzzy_match("CEO of Tesla Inc", "CEO Tesla Inc company", 0.5)

    def test_no_match(self):
        assert not _fuzzy_match("born in south africa", "works at google", 0.6)

    def test_empty_strings(self):
        assert not _fuzzy_match("", "something", 0.6)
        assert not _fuzzy_match("something", "", 0.6)


class TestFactRecall:
    def test_all_matched(self):
        expected = [
            {"claim": "CEO of Tesla", "difficulty": "easy"},
            {"claim": "Born in South Africa", "difficulty": "easy"},
        ]
        extracted = [
            {"claim": "CEO of Tesla Inc"},
            {"claim": "Born in South Africa in 1971"},
        ]
        result = compute_fact_recall(expected, extracted)
        assert result["recall"] == 1.0
        assert result["matched_count"] == 2

    def test_partial_match(self):
        expected = [
            {"claim": "CEO of Tesla", "difficulty": "easy"},
            {"claim": "Founded Neuralink", "difficulty": "hard"},
        ]
        extracted = [{"claim": "CEO of Tesla electric vehicles"}]
        result = compute_fact_recall(expected, extracted)
        assert result["recall"] == 0.5

    def test_no_expected(self):
        result = compute_fact_recall([], [{"claim": "something"}])
        assert result["recall"] == 0.0


class TestPrecision:
    def test_all_high_confidence(self):
        facts = [{"confidence": 0.9}, {"confidence": 0.8}]
        result = compute_precision(facts)
        assert result["estimated_precision"] == 1.0

    def test_mixed_confidence(self):
        facts = [{"confidence": 0.9}, {"confidence": 0.3}]
        result = compute_precision(facts)
        assert result["estimated_precision"] == 0.5

    def test_empty(self):
        result = compute_precision([])
        assert result["estimated_precision"] == 0.0


class TestF1:
    def test_perfect_scores(self):
        assert compute_f1(1.0, 1.0) == 1.0

    def test_zero_scores(self):
        assert compute_f1(0.0, 0.0) == 0.0

    def test_balanced(self):
        f1 = compute_f1(0.8, 0.6)
        assert 0.6 < f1 < 0.8


class TestEvaluateRisks:
    def test_matching_risks(self):
        expected = ["Regulatory scrutiny", "Financial risk"]
        identified = [
            {"description": "Subject faces regulatory scrutiny from SEC", "risk_category": "legal"},
            {"description": "High financial risk exposure", "risk_category": "financial"},
        ]
        result = evaluate_risks(expected, identified)
        assert result["risk_recall"] == 1.0

    def test_no_match(self):
        expected = ["Cybersecurity vulnerability"]
        identified = [
            {"description": "Financial misconduct allegations", "risk_category": "financial"}
        ]
        result = evaluate_risks(expected, identified)
        assert result["risk_recall"] == 0.0
