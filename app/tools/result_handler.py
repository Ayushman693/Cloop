"""Normalizes raw execution outcomes into a structured `ToolResult`.

Every path that can produce a tool outcome (unknown tool, failed
validation, a tool raising, a tool succeeding) goes through this
module so the shape handed back to the model is always consistent:
`{tool_call_id, status, output, error}`.
"""

from __future__ import annotations

from typing import Any

from app.models.tool_result import ToolErrorDetail, ToolResult


class ResultHandler:
    """Builds `ToolResult` instances for success and failure outcomes."""

    @staticmethod
    def success(tool_call_id: str, name: str, output: Any) -> ToolResult:
        return ToolResult(
            tool_call_id=tool_call_id,
            name=name,
            status="success",
            output=output,
            error=None,
        )

    @staticmethod
    def failure(tool_call_id: str, name: str, error_type: str, message: str) -> ToolResult:
        return ToolResult(
            tool_call_id=tool_call_id,
            name=name,
            status="error",
            output=None,
            error=ToolErrorDetail(type=error_type, message=message),
        )
