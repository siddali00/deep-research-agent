from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.graphs.state import ResearchState
from src.tools.search import TavilySearchTool

logger = logging.getLogger(__name__)


def searcher_node(state: ResearchState) -> dict:
    """Execute all planned search queries via Tavily concurrently."""
    queries = state.get("research_plan", [])
    logger.info("Searcher node: executing %d queries", len(queries))

    tool = TavilySearchTool()
    executed_queries = {sh["query"] for sh in state.get("search_history", [])}
    new_queries = [q for q in queries if q not in executed_queries]

    if not new_queries:
        logger.info("All queries already executed, skipping")
        return {"search_history": [], "status": "extracting"}

    new_results = []

    def _run_search(query: str) -> dict:
        try:
            results = tool.search(query=query, max_results=5)
            logger.info("Query '%s' returned %d results", query, len(results))
            return {"query": query, "results": results}
        except Exception as e:
            logger.error("Search failed for query '%s': %s", query, e)
            return {"query": query, "results": []}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_run_search, q): q for q in new_queries}
        for future in as_completed(futures):
            new_results.append(future.result())

    return {
        "search_history": new_results,
        "status": "extracting",
    }
