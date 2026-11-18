"""Registration and lookup of available tools.

Deliberately separate from `ToolExecutor`: the registry only knows what
tools exist and their schemas. It has no knowledge of how a `ToolCall`
flows through execution or error handling.
"""

from __future__ import annotations

from typing import Any

from app.core.exceptions import ToolNotFoundError
from app.tools.base import BaseTool


class ToolRegistry:
    """Holds the set of tools available to the agent for a given run."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Add a tool to the registry, keyed by its `name`."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        """Look up a tool by name.

        Raises:
            ToolNotFoundError: if no tool with that name is registered.
        """
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolNotFoundError(f"No tool registered with name '{name}'") from exc

    def list_definitions(self) -> list[dict[str, Any]]:
        """Return the schema of every registered tool, for the model."""
        return [tool.definition() for tool in self._tools.values()]
