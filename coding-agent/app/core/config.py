"""Agent-level configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration controlling the behavior of an `AgentLoop` run.

    Kept intentionally small. Provider-specific settings (API keys,
    endpoints, sampling parameters) belong to the concrete `ModelClient`,
    not here.
    """

    max_iterations: int = Field(default=10, gt=0)
    model_name: str = "unset"
