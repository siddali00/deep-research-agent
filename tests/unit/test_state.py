from src.graphs.state import (
    ResearchState,
    ExtractedFact,
    RiskFlag,
    Connection,
    SearchResult,
    _merge_lists,
    _merge_dicts,
)


class TestReducers:
    def test_merge_lists(self):
        assert _merge_lists([1, 2], [3, 4]) == [1, 2, 3, 4]
        assert _merge_lists([], [1]) == [1]
        assert _merge_lists([1], []) == [1]

    def test_merge_dicts(self):
        assert _merge_dicts({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}
        assert _merge_dicts({"a": 1}, {"a": 2}) == {"a": 2}


class TestStateTypes:
    def test_extracted_fact_structure(self):
        fact: ExtractedFact = {
            "category": "professional",
            "claim": "CEO of Test Corp",
            "source_url": "https://example.com",
            "source_title": "Example Article",
            "date_mentioned": "2024-01-01",
            "entities": ["Test Corp"],
            "confidence": 0.85,
        }
        assert fact["category"] == "professional"
        assert fact["confidence"] == 0.85

    def test_risk_flag_structure(self):
        risk: RiskFlag = {
            "risk_category": "financial",
            "severity": "high",
            "description": "Undisclosed investments",
            "supporting_facts": [0, 3, 7],
            "recommendations": ["Review SEC filings"],
        }
        assert risk["severity"] == "high"

    def test_connection_structure(self):
        conn: Connection = {
            "source_entity": "Person A",
            "target_entity": "Company B",
            "relationship": "WORKS_AT",
            "description": "Current CEO",
            "confidence": 0.9,
        }
        assert conn["relationship"] == "WORKS_AT"
