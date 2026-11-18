"""Demonstration tool: counts characters in a string."""

from __future__ import annotations

from app.tools.base import BaseTool
from app.tools.schema_generator import SchemaGenerator, ToolParameter


class TextLengthTool(BaseTool):
    """Returns the number of characters in a given string."""

    name = "text_length"
    description = "Return the character count of the given text."
    parameters = SchemaGenerator.generate(
        [
            ToolParameter(name="text", type="string", description="The text to measure."),
        ]
    )

    def run(self, text: str) -> dict:
        return {"length": len(text)}
