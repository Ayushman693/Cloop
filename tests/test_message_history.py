import json

from app.context.message_history import MessageHistory
from app.models.tool_call import ToolCall
from app.models.tool_result import ToolResult


def test_add_user_and_assistant_messages():
    history = MessageHistory()
    history.add_user("hello")
    history.add_assistant(content="hi there")

    messages = history.get_messages()
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "hello"
    assert messages[1].role == "assistant"
    assert messages[1].content == "hi there"


def test_assistant_message_with_tool_calls():
    history = MessageHistory()
    tool_call = ToolCall(id="call_1", name="add", arguments={"a": 1, "b": 2})
    history.add_assistant(content=None, tool_calls=[tool_call])

    messages = history.get_messages()
    assert messages[0].tool_calls == [tool_call]


def test_tool_result_is_appended_as_tool_message():
    history = MessageHistory()
    result = ToolResult(tool_call_id="call_1", name="add", status="success", output=3)
    history.add_tool_result(result)

    messages = history.get_messages()
    assert len(messages) == 1
    assert messages[0].role == "tool"
    assert messages[0].tool_call_id == "call_1"
    assert messages[0].name == "add"

    payload = json.loads(messages[0].content)
    assert payload["status"] == "success"
    assert payload["output"] == 3
    assert payload["error"] is None


def test_get_messages_returns_a_copy():
    history = MessageHistory()
    history.add_user("hello")
    messages = history.get_messages()
    messages.append(None)
    assert len(history.get_messages()) == 1


def test_clear_empties_history():
    history = MessageHistory()
    history.add_user("hello")
    history.clear()
    assert len(history) == 0
