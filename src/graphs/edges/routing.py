from __future__ import annotations

import logging

from src.graphs.state import ResearchState

logger = logging.getLogger(__name__)


def route_after_validation(state: ResearchState) -> str:
    """Decide whether to continue researching or generate the final report.

    Returns the name of the next node: "planner" or "reporter".
    """
    status = state.get("status", "")

    if status == "reporting":
        logger.info("Routing to reporter (research sufficient or max iterations reached)")
        return "reporter"

    logger.info("Routing back to planner (more research needed)")
    return "planner"
