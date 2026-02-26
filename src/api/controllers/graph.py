from __future__ import annotations

import logging

from src.db.queries.identity_graph import IdentityGraphQueries

logger = logging.getLogger(__name__)


def get_graph_data(research_id: str) -> dict:
    """Retrieve the identity graph for a given research subject."""
    try:
        queries = IdentityGraphQueries()
        return queries.get_full_graph()
    except Exception as e:
        logger.error("Failed to retrieve graph data: %s", e)
        return {"nodes": [], "relationships": [], "error": str(e)}
