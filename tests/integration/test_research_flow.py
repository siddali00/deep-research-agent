"""Integration tests for the research flow.

These tests require API keys and external services to be configured.
Run with: pytest tests/integration/ -v
"""
import pytest
import os

from src.config.settings import get_settings


def _has_api_keys() -> bool:
    try:
        settings = get_settings()
        return bool(settings.openrouter_api_key and settings.tavily_api_key)
    except Exception:
        return False


@pytest.mark.skipif(not _has_api_keys(), reason="API keys not configured")
class TestResearchFlowIntegration:
    def test_build_research_graph(self):
        from src.graphs.research_graph import build_research_graph
        graph = build_research_graph()
        assert graph is not None

    def test_model_router_creates_models(self):
        from src.models.router import ModelRouter
        from src.config.models import TaskType
        router = ModelRouter()
        model = router.get_model(TaskType.PLANNING)
        assert model is not None

    def test_tavily_search(self):
        from src.tools.search import TavilySearchTool
        tool = TavilySearchTool()
        results = tool.search("Python programming language", max_results=3)
        assert len(results) > 0
        assert "title" in results[0]
        assert "url" in results[0]


class TestFastAPIApp:
    def test_app_creates_successfully(self):
        os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
        os.environ.setdefault("GOOGLE_API_KEY", "test-key")
        os.environ.setdefault("TAVILY_API_KEY", "test-key")
        from src.api.app import create_app
        app = create_app()
        assert app is not None
        assert app.title == "Deep Research AI Agent"
