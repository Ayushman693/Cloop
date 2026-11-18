from app.models.tool_call import ToolCall
from app.tools.base import BaseTool
from app.tools.dispatcher import ToolDispatcher
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry


class AddTool(BaseTool):
    name = "add"
    description = "Add two integers."
    parameters = {
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
        "additionalProperties": False,
    }

    def run(self, a: int, b: int) -> int:
        return a + b


def _make_dispatcher():
    registry = ToolRegistry()
    registry.register(AddTool())
    return ToolDispatcher(registry, ToolExecutor())


def test_dispatch_successful_call():
    dispatcher = _make_dispatcher()
    tool_call = ToolCall(id="call_1", name="add", arguments={"a": 2, "b": 3})

    result = dispatcher.dispatch(tool_call)

    assert result.status == "success"
    assert result.output == 5
    assert result.tool_call_id == "call_1"


def test_dispatch_unknown_tool_name_returns_error_result():
    dispatcher = _make_dispatcher()
    tool_call = ToolCall(id="call_1", name="does_not_exist", arguments={})

    result = dispatcher.dispatch(tool_call)

    assert result.status == "error"
    assert result.error.type == "ToolNotFoundError"
    assert result.tool_call_id == "call_1"


def test_dispatch_rejects_invalid_arguments_before_executing():
    dispatcher = _make_dispatcher()
    tool_call = ToolCall(id="call_1", name="add", arguments={"a": 1})

    result = dispatcher.dispatch(tool_call)

    assert result.status == "error"
    assert result.error.type == "ValidationError"
    assert "b" in result.error.message


def test_dispatch_rejects_unexpected_arguments():
    dispatcher = _make_dispatcher()
    tool_call = ToolCall(id="call_1", name="add", arguments={"a": 1, "b": 2, "c": 3})

    result = dispatcher.dispatch(tool_call)

    assert result.status == "error"
    assert result.error.type == "ValidationError"
    assert "c" in result.error.message


def test_dispatch_all_preserves_order_and_tool_call_ids():
    dispatcher = _make_dispatcher()
    calls = [
        ToolCall(id="call_1", name="add", arguments={"a": 1, "b": 1}),
        ToolCall(id="call_2", name="add", arguments={"a": 10, "b": 10}),
    ]

    results = dispatcher.dispatch_all(calls)

    assert [r.tool_call_id for r in results] == ["call_1", "call_2"]
    assert [r.output for r in results] == [2, 20]
