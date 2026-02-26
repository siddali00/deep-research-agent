"""Resilient LLM invocation with retry and cross-provider fallback."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel

from src.config.models import TaskType
from src.models.router import ModelRouter

logger = logging.getLogger(__name__)


def resilient_invoke(
    router: ModelRouter,
    task: TaskType,
    messages: Any,
    *,
    temperature: float = 0.0,
    json_mode: bool = False,
):
    """Invoke an LLM with retry + cross-provider fallback.

    Strategy:
    1. Call the primary model (from TASK_MODEL_MAP).
    2. On any error, retry the primary model once.
    3. If retry fails, fall back to the alternate provider.
    4. If fallback also fails, return None.
    """
    primary = router.get_model(task, temperature=temperature, json_mode=json_mode)

    # Attempt 1: primary
    try:
        return primary.invoke(messages)
    except Exception as e:
        logger.warning("Primary invoke failed for %s: %s. Retrying...", task.value, e)

    # Attempt 2: primary retry
    try:
        return primary.invoke(messages)
    except Exception as e:
        logger.warning("Primary retry failed for %s: %s. Falling back...", task.value, e)

    # Attempt 3: fallback provider
    try:
        fallback = router.get_fallback_model(task, temperature=temperature, json_mode=json_mode)
        return fallback.invoke(messages)
    except Exception as e:
        logger.error("Fallback invoke failed for %s: %s. Giving up.", task.value, e)

    return None
