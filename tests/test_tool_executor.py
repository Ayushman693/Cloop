from app.models.tool_call import ToolCall
from app.tools.base import BaseTool
from app.tools.executor import ToolExecutor


class AddTool(BaseTool):
    name = "add"
    description = "Add two integers."
    parameters = {
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    }

    def run(self, a: int, b: int) -> int:
        return a + b


class FailingTool(BaseTool):
    name = "boom"
    description = "Always raises."
    parameters = {"type": "object", "properties": {}}

    def run(self, **kwargs) -> int:
        raise ValueError("bad input")


def test_execute_successful_tool():
    executor = ToolExecutor()
    tool_call = ToolCall(id="call_1", name="add", arguments={"a": 2, "b": 3})

    result = executor.execute(AddTool(), tool_call)

    assert result.status == "success"
    assert result.output == 5
    assert result.tool_call_id == "call_1"


def test_execute_captures_exception_without_raising():
    executor = ToolExecutor()
    tool_call = ToolCall(id="call_1", name="boom", arguments={})

    result = executor.execute(FailingTool(), tool_call)

    assert result.status == "error"
    assert result.error.type == "ValueError"
    assert result.error.message == "bad input"
    assert result.tool_call_id == "call_1"


def test_execute_preserves_tool_call_id_across_multiple_calls():
    executor = ToolExecutor()
    tool = AddTool()
    calls = [
        ToolCall(id="call_1", name="add", arguments={"a": 1, "b": 1}),
        ToolCall(id="call_2", name="add", arguments={"a": 2, "b": 2}),
    ]

    results = [executor.execute(tool, call) for call in calls]

    assert [r.tool_call_id for r in results] == ["call_1", "call_2"]
    assert [r.output for r in results] == [2, 4]
