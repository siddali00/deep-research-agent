"""Helpers for normalizing LLM response content across model providers."""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)


def _part_to_str(part) -> str | None:
    """Extract text from a single content part, returning None for non-text blocks.

    Handles:
    - Plain strings
    - Gemini / OpenAI content parts: {'type': 'text', 'text': '...'}
    - Reasoning blocks from reasoning models: {'type': 'reasoning', ...} -> skipped
    """
    if isinstance(part, str):
        return part
    if isinstance(part, dict):
        if part.get("type") == "reasoning":
            return None
        if "text" in part:
            return part["text"]
    return None


def ensure_str(content) -> str:
    """Convert LLM response content to a plain string.

    Handles shapes returned by different providers / reasoning models:
    - str  (most common)
    - list[str]
    - list[dict] with 'text' keys (Gemini / OpenAI content parts)
    - list containing reasoning blocks (silently skipped)
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [_part_to_str(p) for p in content]
        return "\n".join(p for p in parts if p is not None)
    if isinstance(content, dict):
        if content.get("type") == "reasoning":
            return ""
        if "text" in content:
            return content["text"]
    return str(content)


def strip_code_fences(content) -> str:
    """Normalize content to string and remove markdown code fences if present."""
    text = ensure_str(content).strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return text.strip()


def _fix_unquoted_keys(text: str) -> str:
    """Attempt to fix JSON with unquoted keys like {continue: true}."""
    return re.sub(
        r'(?<=[{,])\s*(\w+)\s*:',
        r' "\1":',
        text,
    )


def _extract_json_block(text: str):
    """Try to find a JSON array or object embedded in free-form text."""
    for pattern in [
        r'(\[[\s\S]*\])',  # outermost [...] 
        r'(\{[\s\S]*\})',  # outermost {...}
    ]:
        m = re.search(pattern, text)
        if m:
            candidate = m.group(1)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                try:
                    return json.loads(_fix_unquoted_keys(candidate))
                except json.JSONDecodeError:
                    continue
    return None


def robust_json_loads(content, *, context: str = ""):
    """Best-effort parse of LLM output into a Python object.

    Tries, in order:
    1. Direct json.loads after stripping code fences
    2. Fixing unquoted keys then json.loads
    3. Regex extraction of JSON array/object from surrounding prose
    Returns the parsed object, or None on failure (with debug logging).
    """
    text = strip_code_fences(content)

    # 1. Direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # 2. Fix unquoted keys
    try:
        return json.loads(_fix_unquoted_keys(text))
    except (json.JSONDecodeError, TypeError):
        pass

    # 3. Regex extraction from surrounding narrative
    extracted = _extract_json_block(text)
    if extracted is not None:
        return extracted

    logger.warning(
        "robust_json_loads failed (%s). First 500 chars of response:\n%s",
        context,
        text[:500],
    )
    return None
