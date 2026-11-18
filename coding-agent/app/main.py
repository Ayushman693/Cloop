"""Entry point demonstrating how the components wire together.

No concrete LLM provider is implemented yet (see app/llm/provider_adapter.py),
so this uses a trivial local `EchoModelClient` that always returns a final
response immediately. It exists only to prove the wiring runs end to end
without requiring API keys; it is not meant to be a real agent.
"""

from __future__ import annotations

from typing import Any

from app.context.message_history import MessageHistory
from app.core.agent_loop import AgentLoop
from app.core.config import AgentConfig
from app.llm.base import ModelClient
from app.models.messages import Message
from app.models.responses import ModelResponse
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry


class EchoModelClient(ModelClient):
    """Always returns a final response, echoing the last user message."""

    def generate(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        last_user = next(
            (m for m in reversed(messages) if m.role == "user"), None
        )
        content = f"Echo: {last_user.content}" if last_user else "No input received."
        return ModelResponse(content=content, finish_reason="stop")


def build_agent_loop() -> AgentLoop:
    """Wire up the default, provider-less agent loop."""
    registry = ToolRegistry()
    return AgentLoop(
        model_client=EchoModelClient(),
        tool_registry=registry,
        tool_executor=ToolExecutor(registry),
        config=AgentConfig(max_iterations=10, model_name="echo-demo"),
        history=MessageHistory(),
    )


def main() -> None:
    agent = build_agent_loop()
    response = agent.run("Hello, agent harness.")
    print(response)


if __name__ == "__main__":
    main()
