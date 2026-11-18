"""Resolves and executes tool calls against the registry.

Separate from `ToolRegistry` so that execution concerns (argument
validation, error containment) don't leak into tool bookkeeping.
"""

from __future__ import annotations

from app.core.exceptions import ToolNotFoundError
from app.models.tool_call import ToolCall, ToolResult
from app.tools.registry import ToolRegistry


class ToolExecutor:
    """Executes a `ToolCall` and always returns a structured `ToolResult`.

    Tool execution errors (missing tool, bad arguments, runtime
    exceptions) are caught here and converted into an error
    `ToolResult` rather than propagating, so one failing tool call
    cannot crash the agent loop.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """Resolve `tool_call` via the registry and run it."""
        try:
            tool = self._registry.get(tool_call.name)
        except ToolNotFoundError as exc:
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=str(exc),
                is_error=True,
            )

        try:
            output = tool.run(**tool_call.arguments)
        except Exception as exc:  # noqa: BLE001 - intentional: contain any tool failure
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=f"Tool '{tool_call.name}' raised an error: {exc}",
                is_error=True,
            )

        return ToolResult(
            tool_call_id=tool_call.id,
            name=tool_call.name,
            content=output,
            is_error=False,
        )
