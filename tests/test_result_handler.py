from app.tools.result_handler import ResultHandler


def test_success_result_shape():
    result = ResultHandler.success("call_1", "add", {"result": 75})

    assert result.tool_call_id == "call_1"
    assert result.name == "add"
    assert result.status == "success"
    assert result.output == {"result": 75}
    assert result.error is None
    assert result.is_error is False


def test_failure_result_shape():
    result = ResultHandler.failure("call_1", "add", "ValueError", "bad input")

    assert result.tool_call_id == "call_1"
    assert result.status == "error"
    assert result.output is None
    assert result.error.type == "ValueError"
    assert result.error.message == "bad input"
    assert result.is_error is True
