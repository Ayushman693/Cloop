"""Executes a single, already-resolved tool call.

Deliberately has no dependency on `ToolRegistry`: resolving a tool call
to a `BaseTool` is the `ToolDispatcher`'s job. This keeps execution and
registration independently testable and satisfies the architectural
constraint that `ToolRegistry` and `ToolExecutor` stay decoupled.
"""

from __future__ import annotations

from app.models.tool_call import ToolCall
from app.models.tool_result import ToolResult
from app.tools.base import BaseTool
from app.tools.result_handler import ResultHandler


class ToolExecutor:
    """Runs a resolved `BaseTool` and always returns a structured `ToolResult`.

    Any exception raised by the tool's `run` implementation is caught
    here and converted into an error `ToolResult` rather than
    propagating, so one failing tool call cannot crash the agent loop.
    Stateless, so it's safe to call repeatedly for multiple tool calls
    in the same model turn.
    """

    def execute(self, tool: BaseTool, tool_call: ToolCall) -> ToolResult:
        """Run `tool` with `tool_call.arguments`, preserving `tool_call.id`."""
        try:
            output = tool.run(**tool_call.arguments)
        except Exception as exc:  # noqa: BLE001 - intentional: contain any tool failure
            return ResultHandler.failure(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                error_type=type(exc).__name__,
                message=str(exc),
            )

        return ResultHandler.success(
            tool_call_id=tool_call.id,
            name=tool_call.name,
            output=output,
        )
