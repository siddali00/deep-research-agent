from tavily import TavilyClient

from src.config.settings import get_settings


class TavilySearchTool:
    """Wraps the Tavily API for deep web search."""

    def __init__(self):
        settings = get_settings()
        self._client = TavilyClient(api_key=settings.tavily_api_key)

    def search(
        self,
        query: str,
        max_results: int = 10,
        search_depth: str = "advanced",
        include_raw_content: bool = False,
    ) -> list[dict]:
        response = self._client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_raw_content=include_raw_content,
        )
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "score": r.get("score", 0.0),
                "raw_content": r.get("raw_content"),
            }
            for r in response.get("results", [])
        ]

    def search_context(self, query: str, max_results: int = 5) -> str:
        """Returns a single concatenated string of search results for LLM context."""
        return self._client.get_search_context(
            query=query,
            max_results=max_results,
            search_depth="advanced",
        )
