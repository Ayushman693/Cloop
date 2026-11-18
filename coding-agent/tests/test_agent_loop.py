import pytest

from app.core.agent_loop import AgentLoop
from app.core.config import AgentConfig
from app.core.exceptions import MaxIterationsExceededError
from app.models.responses import ModelResponse
from app.models.tool_call import ToolCall
from app.tools.base import BaseTool
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry

from tests.mock_model_client import MockModelClient


class AddTool(BaseTool):
    name = "add"
    description = "Add two integers."
    parameters = {
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    }

    def run(self, a: int, b: int) -> str:
        return str(a + b)


class FailingTool(BaseTool):
    name = "boom"
    description = "Always raises."
    parameters = {"type": "object", "properties": {}}

    def run(self, **kwargs) -> str:
        raise RuntimeError("something went wrong")


def _make_loop(model_client, registry=None, max_iterations=10):
    registry = registry or ToolRegistry()
    return AgentLoop(
        model_client=model_client,
        tool_registry=registry,
        tool_executor=ToolExecutor(registry),
        config=AgentConfig(max_iterations=max_iterations),
    )


def test_final_response_without_tool_calls():
    client = MockModelClient(
        [ModelResponse(content="Hello!", finish_reason="stop")]
    )
    loop = _make_loop(client)

    result = loop.run("hi")

    assert result == "Hello!"
    assert len(client.calls) == 1


def test_single_tool_call_then_final_response():
    registry = ToolRegistry()
    registry.register(AddTool())

    tool_call = ToolCall(id="call_1", name="add", arguments={"a": 2, "b": 3})
    client = MockModelClient(
        [
            ModelResponse(content=None, tool_calls=[tool_call], finish_reason="tool_calls"),
            ModelResponse(content="The sum is 5.", finish_reason="stop"),
        ]
    )
    loop = _make_loop(client, registry=registry)

    result = loop.run("add 2 and 3")

    assert result == "The sum is 5."
    assert len(client.calls) == 2
    tool_messages = [m for m in loop.history.get_messages() if m.role == "tool"]
    assert len(tool_messages) == 1
    assert tool_messages[0].content == "5"


def test_multiple_tool_calls_in_one_turn():
    registry = ToolRegistry()
    registry.register(AddTool())

    calls = [
        ToolCall(id="call_1", name="add", arguments={"a": 1, "b": 1}),
        ToolCall(id="call_2", name="add", arguments={"a": 10, "b": 10}),
    ]
    client = MockModelClient(
        [
            ModelResponse(content=None, tool_calls=calls, finish_reason="tool_calls"),
            ModelResponse(content="Done.", finish_reason="stop"),
        ]
    )
    loop = _make_loop(client, registry=registry)

    result = loop.run("do two additions")

    assert result == "Done."
    tool_messages = [m for m in loop.history.get_messages() if m.role == "tool"]
    assert [m.content for m in tool_messages] == ["2", "20"]


def test_tool_execution_failure_is_captured_without_crashing():
    registry = ToolRegistry()
    registry.register(FailingTool())

    tool_call = ToolCall(id="call_1", name="boom", arguments={})
    client = MockModelClient(
        [
            ModelResponse(content=None, tool_calls=[tool_call], finish_reason="tool_calls"),
            ModelResponse(content="Recovered.", finish_reason="stop"),
        ]
    )
    loop = _make_loop(client, registry=registry)

    result = loop.run("trigger failure")

    assert result == "Recovered."
    tool_messages = [m for m in loop.history.get_messages() if m.role == "tool"]
    assert len(tool_messages) == 1
    assert "something went wrong" in tool_messages[0].content


def test_max_iterations_exceeded_raises():
    tool_call = ToolCall(id="call_1", name="add", arguments={"a": 1, "b": 1})
    registry = ToolRegistry()
    registry.register(AddTool())

    client = MockModelClient(
        [
            ModelResponse(content=None, tool_calls=[tool_call], finish_reason="tool_calls")
            for _ in range(3)
        ]
    )
    loop = _make_loop(client, registry=registry, max_iterations=3)

    with pytest.raises(MaxIterationsExceededError):
        loop.run("loop forever")


def test_history_accumulates_user_assistant_and_tool_messages_in_order():
    registry = ToolRegistry()
    registry.register(AddTool())

    tool_call = ToolCall(id="call_1", name="add", arguments={"a": 4, "b": 5})
    client = MockModelClient(
        [
            ModelResponse(content=None, tool_calls=[tool_call], finish_reason="tool_calls"),
            ModelResponse(content="9.", finish_reason="stop"),
        ]
    )
    loop = _make_loop(client, registry=registry)

    loop.run("add 4 and 5")

    roles = [m.role for m in loop.history.get_messages()]
    assert roles == ["user", "assistant", "tool", "assistant"]


def test_loop_terminates_on_first_final_response_without_extra_calls():
    client = MockModelClient(
        [ModelResponse(content="done", finish_reason="stop")]
    )
    loop = _make_loop(client, max_iterations=50)

    loop.run("anything")

    assert len(client.calls) == 1
