"""Abstract interface every model provider must implement."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.messages import Message
from app.models.responses import ModelResponse


class ModelClient(ABC):
    """Provider-independent contract for calling an LLM.

    Implementations are responsible for translating `messages` and
    `tools` into their provider's request format, and for normalizing
    the provider's raw reply into a `ModelResponse`. The `AgentLoop`
    only ever depends on this interface, never on a concrete provider.
    """

    @abstractmethod
    def generate(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        """Send the conversation to the model and return a normalized response.

        Args:
            messages: Full conversation history to send to the model.
            tools: Tool definitions (name/description/parameters schema)
                the model may choose to call.

        Returns:
            A `ModelResponse` describing either a final answer or
            requested tool calls.
        """
        raise NotImplementedError
