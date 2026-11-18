"""Conversation message model."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

from app.models.tool_call import ToolCall

Role = Literal["system", "user", "assistant", "tool"]


class Message(BaseModel):
    """A single message in the conversation history.

    `tool_calls` is populated on assistant messages that request tool
    execution. `tool_call_id` and `name` are populated on tool-role
    messages so the result can be matched back to its originating call.
    """

    role: Role
    content: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
