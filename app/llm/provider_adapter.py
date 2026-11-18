"""Scaffold for adapting a concrete provider SDK to the `ModelClient` interface.

No concrete provider (OpenAI, Anthropic, etc.) is wired up in this phase.
A future `ModelClient` implementation for a specific provider should:

1. Translate `list[Message]` into that provider's request message format.
2. Translate `tools` definitions into that provider's tool/function-calling
   schema.
3. Call the provider SDK.
4. Normalize the raw reply into a `ModelResponse` via
   `ResponseNormalizer`, which extracts tool calls into `list[ToolCall]`
   and handles JSON-string-encoded arguments.

Keeping this translation in one place is what lets `AgentLoop` stay
provider-agnostic: swapping providers means writing a new adapter here,
not touching the loop.
"""

from __future__ import annotations

from typing import Any

from app.llm.base import ModelClient
from app.models.messages import Message
from app.models.responses import ModelResponse


class ProviderAdapter(ModelClient):
    """Base class for provider-specific adapters.

    Intentionally unimplemented: concrete subclasses (e.g. an OpenAI or
    Anthropic adapter) are a later phase. This class exists so the
    directory structure and import paths are stable as providers are
    added.
    """

    def generate(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        raise NotImplementedError(
            "No concrete provider adapter is implemented yet. "
            "Subclass ProviderAdapter and implement generate()."
        )
