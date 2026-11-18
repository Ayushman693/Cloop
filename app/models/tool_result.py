"""Structured outcome of executing a `ToolCall`."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel


class ToolErrorDetail(BaseModel):
    """Error information attached to a failed `ToolResult`."""

    type: str
    message: str


class ToolResult(BaseModel):
    """The normalized outcome of dispatching a single `ToolCall`.

    Exactly one of `output`/`error` is populated, matching `status`.
    This is the shape produced by `ResultHandler` and fed back to the
    model, so both the LLM and any calling code see a consistent
    success/error/output/error-detail structure regardless of which
    tool ran or how it failed.
    """

    tool_call_id: str
    name: str
    status: Literal["success", "error"]
    output: Optional[Any] = None
    error: Optional[ToolErrorDetail] = None

    @property
    def is_error(self) -> bool:
        return self.status == "error"

    def to_content(self) -> str:
        """Serialize to the JSON string sent back to the model as tool output."""
        return self.model_dump_json(exclude={"name"})
