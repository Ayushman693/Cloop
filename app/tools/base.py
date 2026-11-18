"""Base interface every tool implementation must satisfy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """A single callable tool exposed to the model.

    Subclasses provide `name`, `description`, and a JSON Schema
    `parameters` dict describing their arguments, plus a `run`
    implementation. No file, shell, or network tools are implemented in
    this phase — this is purely the interface new tools will plug into.
    """

    name: str
    description: str
    parameters: dict[str, Any] = {"type": "object", "properties": {}}

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """Execute the tool and return a JSON-serializable result.

        Raising an exception here is expected behavior for failure
        cases; the `ToolExecutor` is responsible for catching it and
        turning it into a structured `ToolResult`.
        """
        raise NotImplementedError

    def definition(self) -> dict[str, Any]:
        """Return the schema describing this tool to the model."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
