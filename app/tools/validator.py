"""Validates tool-call arguments against a tool's JSON Schema.

Deliberately independent of `ToolRegistry` and `ToolExecutor`: given a
schema dict and an arguments dict, it only answers "is this valid" and
why not — it never looks up or runs anything.
"""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel

_TYPE_CHECKS: dict[str, Callable[[Any], bool]] = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
}


class ValidationError(BaseModel):
    """A single argument validation failure."""

    parameter: str
    message: str


class ArgumentValidator:
    """Validates a tool call's arguments against a JSON Schema object."""

    @staticmethod
    def validate(schema: dict[str, Any], arguments: dict[str, Any]) -> list[ValidationError]:
        """Return the list of validation errors (empty if `arguments` is valid).

        Checks, in order: missing required parameters, unexpected
        parameters (when the schema disallows `additionalProperties`),
        and type mismatches for every recognized parameter.
        """
        errors: list[ValidationError] = []
        properties: dict[str, Any] = schema.get("properties", {})
        required: list[str] = schema.get("required", [])
        additional_allowed = schema.get("additionalProperties", True)

        for name in required:
            if name not in arguments:
                errors.append(
                    ValidationError(parameter=name, message="missing required parameter")
                )

        for name, value in arguments.items():
            if name not in properties:
                if not additional_allowed:
                    errors.append(
                        ValidationError(parameter=name, message="unexpected parameter")
                    )
                continue

            expected_type = properties[name].get("type")
            check = _TYPE_CHECKS.get(expected_type)
            if check is not None and not check(value):
                errors.append(
                    ValidationError(
                        parameter=name,
                        message=(
                            f"expected type '{expected_type}', "
                            f"got '{type(value).__name__}'"
                        ),
                    )
                )

        return errors
