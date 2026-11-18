import pytest

from app.core.exceptions import ToolAlreadyRegisteredError, ToolNotFoundError
from app.tools.base import BaseTool
from app.tools.registry import ToolRegistry


class AddTool(BaseTool):
    name = "add"
    description = "Add two integers."
    parameters = {
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "integer"},
        },
        "required": ["a", "b"],
    }

    def run(self, a: int, b: int) -> int:
        return a + b


def test_register_and_get_tool():
    registry = ToolRegistry()
    tool = AddTool()
    registry.register(tool)

    assert registry.get("add") is tool


def test_register_duplicate_name_raises():
    registry = ToolRegistry()
    registry.register(AddTool())

    with pytest.raises(ToolAlreadyRegisteredError):
        registry.register(AddTool())


def test_unregister_removes_tool():
    registry = ToolRegistry()
    registry.register(AddTool())

    registry.unregister("add")

    with pytest.raises(ToolNotFoundError):
        registry.get("add")


def test_unregister_missing_tool_raises():
    registry = ToolRegistry()
    with pytest.raises(ToolNotFoundError):
        registry.unregister("does_not_exist")


def test_get_missing_tool_raises():
    registry = ToolRegistry()
    with pytest.raises(ToolNotFoundError):
        registry.get("does_not_exist")


def test_list_tools_returns_every_registered_tool():
    registry = ToolRegistry()
    tool = AddTool()
    registry.register(tool)

    assert registry.list_tools() == [tool]


def test_list_definitions_returns_schema_for_each_tool():
    registry = ToolRegistry()
    registry.register(AddTool())

    definitions = registry.list_definitions()
    assert len(definitions) == 1
    assert definitions[0]["name"] == "add"
    assert definitions[0]["description"] == "Add two integers."
    assert "properties" in definitions[0]["parameters"]
