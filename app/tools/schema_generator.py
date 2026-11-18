"""Builds JSON Schema parameter definitions for tools.

Tool authors can still hand-write a raw JSON Schema dict as
`BaseTool.parameters` (as Milestone 1 tools do). `SchemaGenerator` is an
additive convenience: describe parameters declaratively with
`ToolParameter` and get a valid JSON Schema object back, so new tools
don't need to hand-write schema boilerplate.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel

JsonSchemaType = Literal["string", "integer", "number", "boolean", "array", "object"]


class ToolParameter(BaseModel):
    """Declarative description of a single tool parameter."""

    name: str
    type: JsonSchemaType
    description: str = ""
    required: bool = True
    items: Optional[dict[str, Any]] = None
    """JSON Schema for array element type. Used when `type == "array"`."""
    properties: Optional[dict[str, Any]] = None
    """JSON Schema properties for a nested object. Used when `type == "object"`."""


class SchemaGenerator:
    """Converts a list of `ToolParameter` into a JSON Schema object."""

    @staticmethod
    def generate(
        parameters: list[ToolParameter],
        additional_properties: bool = False,
    ) -> dict[str, Any]:
        """Build the `parameters` JSON Schema object for a tool definition."""
        properties: dict[str, Any] = {}
        required: list[str] = []

        for parameter in parameters:
            properties[parameter.name] = SchemaGenerator._property_schema(parameter)
            if parameter.required:
                required.append(parameter.name)

        schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
            "additionalProperties": additional_properties,
        }
        if required:
            schema["required"] = required
        return schema

    @staticmethod
    def _property_schema(parameter: ToolParameter) -> dict[str, Any]:
        schema: dict[str, Any] = {"type": parameter.type}
        if parameter.description:
            schema["description"] = parameter.description

        if parameter.type == "array":
            schema["items"] = parameter.items or {"type": "string"}
        elif parameter.type == "object":
            schema["properties"] = parameter.properties or {}
            schema["additionalProperties"] = False

        return schema
