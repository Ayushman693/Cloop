"""Test double for `ModelClient` that returns a scripted sequence of responses.

No network access or API key is required: each call to `generate` pops
the next `ModelResponse` off a predetermined queue, so tests can script
exact agent-loop behavior (e.g. "first turn requests a tool, second
turn returns a final answer").
"""

from __future__ import annotations

from typing import Any

from app.llm.base import ModelClient
from app.models.messages import Message
from app.models.responses import ModelResponse


class MockModelClient(ModelClient):
    """Returns responses from a fixed queue, in order, one per call."""

    def __init__(self, responses: list[ModelResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[list[Message]] = []

    def generate(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        self.calls.append(messages)
        if not self._responses:
            raise AssertionError(
                "MockModelClient.generate called more times than it has "
                "scripted responses for."
            )
        return self._responses.pop(0)
