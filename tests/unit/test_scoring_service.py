import pytest

from src.services.scoring_service import (
    get_source_tier,
    compute_confidence,
    aggregate_confidence_stats,
)


class TestGetSourceTier:
    def test_tier1_sec(self):
        assert get_source_tier("https://www.sec.gov/cgi-bin/browse-edgar") == 1

    def test_tier2_bloomberg(self):
        assert get_source_tier("https://www.bloomberg.com/news/article") == 2

    def test_tier3_crunchbase(self):
        assert get_source_tier("https://www.crunchbase.com/person/john") == 3

    def test_tier4_linkedin(self):
        assert get_source_tier("https://www.linkedin.com/in/john") == 4

    def test_tier5_reddit(self):
        assert get_source_tier("https://www.reddit.com/r/investing") == 5

    def test_unknown_defaults_to_4(self):
        assert get_source_tier("https://www.randomsite.com") == 4

    def test_empty_url(self):
        assert get_source_tier("") == 5


class TestComputeConfidence:
    def test_no_sources(self):
        assert compute_confidence([]) == 0.3

    def test_single_authoritative(self):
        score = compute_confidence(["https://sec.gov/filing"])
        assert score >= 0.9

    def test_multiple_sources_bonus(self):
        single = compute_confidence(["https://bbc.com/article"], corroboration_count=1)
        multi = compute_confidence(["https://bbc.com/article"], corroboration_count=3)
        assert multi > single

    def test_score_capped_at_1(self):
        score = compute_confidence(
            ["https://sec.gov/filing"] * 5, corroboration_count=10
        )
        assert score <= 1.0


class TestAggregateConfidenceStats:
    def test_empty_facts(self):
        stats = aggregate_confidence_stats([])
        assert stats["total_facts"] == 0
        assert stats["avg_confidence"] == 0.0

    def test_with_facts(self):
        facts = [
            {"category": "biographical", "confidence": 0.9},
            {"category": "professional", "confidence": 0.6},
            {"category": "biographical", "confidence": 0.3},
        ]
        stats = aggregate_confidence_stats(facts)
        assert stats["total_facts"] == 3
        assert stats["high_confidence_count"] == 1
        assert stats["medium_confidence_count"] == 1
        assert stats["low_confidence_count"] == 1
        assert stats["category_breakdown"]["biographical"] == 2
