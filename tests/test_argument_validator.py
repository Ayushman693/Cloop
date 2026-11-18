from app.tools.validator import ArgumentValidator

SCHEMA = {
    "type": "object",
    "properties": {
        "a": {"type": "integer"},
        "b": {"type": "integer"},
        "name": {"type": "string"},
    },
    "required": ["a", "b"],
    "additionalProperties": False,
}


def test_valid_arguments_produce_no_errors():
    errors = ArgumentValidator.validate(SCHEMA, {"a": 1, "b": 2, "name": "x"})
    assert errors == []


def test_missing_required_argument_is_rejected():
    errors = ArgumentValidator.validate(SCHEMA, {"a": 1})
    assert any(e.parameter == "b" and "missing" in e.message for e in errors)


def test_invalid_type_is_rejected():
    errors = ArgumentValidator.validate(SCHEMA, {"a": "not-an-int", "b": 2})
    assert any(e.parameter == "a" and "type" in e.message for e in errors)


def test_unexpected_argument_is_rejected_when_additional_properties_false():
    errors = ArgumentValidator.validate(SCHEMA, {"a": 1, "b": 2, "extra": True})
    assert any(e.parameter == "extra" and "unexpected" in e.message for e in errors)


def test_unexpected_argument_is_allowed_when_additional_properties_true():
    permissive_schema = {**SCHEMA, "additionalProperties": True}
    errors = ArgumentValidator.validate(permissive_schema, {"a": 1, "b": 2, "extra": True})
    assert errors == []


def test_boolean_is_not_mistaken_for_integer():
    errors = ArgumentValidator.validate(SCHEMA, {"a": True, "b": 2})
    assert any(e.parameter == "a" for e in errors)
