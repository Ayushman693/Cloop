"""Ordered conversation history shared between the loop and the model client."""

from __future__ import annotations

from app.models.messages import Message
from app.models.tool_call import ToolCall, ToolResult


class MessageHistory:
    """Accumulates the conversation as an ordered list of `Message`."""

    def __init__(self) -> None:
        self._messages: list[Message] = []

    def add_system(self, content: str) -> None:
        self._messages.append(Message(role="system", content=content))

    def add_user(self, content: str) -> None:
        self._messages.append(Message(role="user", content=content))

    def add_assistant(
        self,
        content: str | None = None,
        tool_calls: list[ToolCall] | None = None,
    ) -> None:
        self._messages.append(
            Message(role="assistant", content=content, tool_calls=tool_calls)
        )

    def add_tool_result(self, result: ToolResult) -> None:
        self._messages.append(
            Message(
                role="tool",
                content=result.content,
                tool_call_id=result.tool_call_id,
                name=result.name,
            )
        )

    def get_messages(self) -> list[Message]:
        """Return a copy of the accumulated messages, in order."""
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)
