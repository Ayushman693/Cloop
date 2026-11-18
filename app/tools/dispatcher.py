"""Orchestrates resolving, validating, and executing tool calls.

This is the one component allowed to depend on both `ToolRegistry` and
`ToolExecutor` — they otherwise know nothing about each other. For each
`ToolCall` it:

1. Resolves the tool name via `ToolRegistry` (unknown name -> error result).
2. Validates arguments via `ArgumentValidator` (invalid args -> error result).
3. Executes via `ToolExecutor` and returns its structured `ToolResult`.
"""

from __future__ import annotations

from app.core.exceptions import ToolNotFoundError
from app.models.tool_call import ToolCall
from app.models.tool_result import ToolResult
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry
from app.tools.result_handler import ResultHandler
from app.tools.validator import ArgumentValidator


class ToolDispatcher:
    """Resolves and runs tool calls requested by the model."""

    def __init__(self, registry: ToolRegistry, executor: ToolExecutor) -> None:
        self._registry = registry
        self._executor = executor

    def dispatch(self, tool_call: ToolCall) -> ToolResult:
        """Resolve, validate, and execute a single `ToolCall`."""
        try:
            tool = self._registry.get(tool_call.name)
        except ToolNotFoundError as exc:
            return ResultHandler.failure(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                error_type="ToolNotFoundError",
                message=str(exc),
            )

        errors = ArgumentValidator.validate(tool.parameters, tool_call.arguments)
        if errors:
            message = "; ".join(f"{e.parameter}: {e.message}" for e in errors)
            return ResultHandler.failure(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                error_type="ValidationError",
                message=message,
            )

        return self._executor.execute(tool, tool_call)

    def dispatch_all(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """Dispatch every tool call requested in a single model turn, in order."""
        return [self.dispatch(tool_call) for tool_call in tool_calls]
