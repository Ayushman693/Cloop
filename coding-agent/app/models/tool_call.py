"""Models describing a requested tool invocation and its outcome."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A single tool invocation requested by the model."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """The outcome of executing a `ToolCall`."""

    tool_call_id: str
    name: str
    content: str
    is_error: bool = False
