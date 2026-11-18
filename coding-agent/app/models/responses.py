"""Normalized response returned by any `ModelClient` implementation."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.tool_call import ToolCall

FinishReason = Literal["stop", "tool_calls", "length", "error"]


class ModelResponse(BaseModel):
    """Provider-agnostic representation of a model turn.

    Every `ModelClient` implementation must normalize its provider's raw
    output into this shape before returning it to the `AgentLoop`.
    """

    content: Optional[str] = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    finish_reason: FinishReason = "stop"
