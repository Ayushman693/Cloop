"""Entry point demonstrating a full tool-calling round trip.

No concrete LLM provider is implemented yet (see app/llm/provider_adapter.py),
so this uses a scripted `DemoModelClient` that requests `CalculatorTool`
on its first turn and returns a final answer on its second, once it has
seen the tool result in the conversation history. It exists to prove the
wiring (registry -> dispatcher -> executor -> history -> back to the
model) runs end to end without requiring API keys.
"""

from __future__ import annotations

from typing import Any

from app.context.message_history import MessageHistory
from app.core.agent_loop import AgentLoop
from app.core.config import AgentConfig
from app.llm.base import ModelClient
from app.models.messages import Message
from app.models.responses import ModelResponse
from app.models.tool_call import ToolCall
from app.tools.dispatcher import ToolDispatcher
from app.tools.executor import ToolExecutor
from app.tools.examples.calculator import CalculatorTool
from app.tools.examples.text_length import TextLengthTool
from app.tools.registry import ToolRegistry


class DemoModelClient(ModelClient):
    """Scripted two-turn client: requests `calculator`, then answers using its result."""

    def __init__(self) -> None:
        self._turn = 0

    def generate(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        self._turn += 1

        if self._turn == 1:
            return ModelResponse(
                content=None,
                tool_calls=[
                    ToolCall(id="call_1", name="calculator", arguments={"a": 5, "b": 7})
                ],
                finish_reason="tool_calls",
            )

        tool_message = next(m for m in reversed(messages) if m.role == "tool")
        return ModelResponse(
            content=f"The result is ready: {tool_message.content}",
            finish_reason="stop",
        )


def build_agent_loop() -> AgentLoop:
    """Wire up the default, provider-less agent loop with the example tools registered."""
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(TextLengthTool())

    return AgentLoop(
        model_client=DemoModelClient(),
        tool_registry=registry,
        tool_dispatcher=ToolDispatcher(registry, ToolExecutor()),
        config=AgentConfig(max_iterations=10, model_name="demo"),
        history=MessageHistory(),
    )


def main() -> None:
    agent = build_agent_loop()
    response = agent.run("What is 5 plus 7?")
    print(response)


if __name__ == "__main__":
    main()
