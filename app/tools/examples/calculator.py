"""Demonstration tool: adds two numbers."""

from __future__ import annotations

from app.tools.base import BaseTool
from app.tools.schema_generator import SchemaGenerator, ToolParameter


class CalculatorTool(BaseTool):
    """Adds two numbers and returns their sum."""

    name = "calculator"
    description = "Add two numbers together and return the sum."
    parameters = SchemaGenerator.generate(
        [
            ToolParameter(name="a", type="number", description="The first addend."),
            ToolParameter(name="b", type="number", description="The second addend."),
        ]
    )

    def run(self, a: float, b: float) -> dict:
        return {"result": a + b}
