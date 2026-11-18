"""Shared helpers for turning a provider's raw tool-call payload into
normalized `ToolCall`/`ModelResponse` objects.

Providers commonly return tool-call arguments as a JSON-encoded string
rather than a dict (e.g. OpenAI-style function calling). Every adapter
needs that same parsing, so it lives here once rather than being
duplicated across provider adapters.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from app.models.responses import FinishReason, ModelResponse
from app.models.tool_call import ToolCall


class ResponseNormalizer:
    """Normalizes a provider's raw reply into a `ModelResponse`."""

    @staticmethod
    def normalize_tool_calls(raw_tool_calls: Optional[list[dict[str, Any]]]) -> list[ToolCall]:
        """Convert a list of raw `{id, name, arguments}`-shaped dicts into `ToolCall`s.

        `arguments` may be a dict already, or a JSON-encoded string (or
        empty/missing), all of which are normalized to a dict.
        """
        if not raw_tool_calls:
            return []

        tool_calls: list[ToolCall] = []
        for raw in raw_tool_calls:
            arguments = raw.get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments) if arguments.strip() else {}
            tool_calls.append(
                ToolCall(id=raw["id"], name=raw["name"], arguments=arguments)
            )
        return tool_calls

    @staticmethod
    def normalize(
        content: Optional[str],
        raw_tool_calls: Optional[list[dict[str, Any]]] = None,
        finish_reason: FinishReason = "stop",
    ) -> ModelResponse:
        """Build a normalized `ModelResponse` from raw provider output."""
        tool_calls = ResponseNormalizer.normalize_tool_calls(raw_tool_calls)
        resolved_finish_reason: FinishReason = "tool_calls" if tool_calls else finish_reason
        return ModelResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=resolved_finish_reason,
        )
