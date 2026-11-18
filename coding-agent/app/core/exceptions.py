"""Exception types raised by the agent harness."""

from __future__ import annotations


class AgentError(Exception):
    """Base class for all agent harness errors."""


class ToolNotFoundError(AgentError):
    """Raised when a requested tool name is not present in the registry."""


class ToolExecutionError(AgentError):
    """Raised when a tool's implementation raises during execution."""


class MaxIterationsExceededError(AgentError):
    """Raised when the agent loop reaches its iteration limit without a final response."""
