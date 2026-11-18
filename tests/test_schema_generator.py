from app.tools.schema_generator import SchemaGenerator, ToolParameter


def test_generates_schema_for_each_supported_type():
    parameters = [
        ToolParameter(name="s", type="string"),
        ToolParameter(name="i", type="integer"),
        ToolParameter(name="n", type="number"),
        ToolParameter(name="b", type="boolean"),
        ToolParameter(name="arr", type="array", items={"type": "integer"}),
        ToolParameter(name="obj", type="object", properties={"x": {"type": "string"}}),
    ]

    schema = SchemaGenerator.generate(parameters)

    assert schema["type"] == "object"
    assert schema["properties"]["s"]["type"] == "string"
    assert schema["properties"]["i"]["type"] == "integer"
    assert schema["properties"]["n"]["type"] == "number"
    assert schema["properties"]["b"]["type"] == "boolean"
    assert schema["properties"]["arr"]["type"] == "array"
    assert schema["properties"]["arr"]["items"] == {"type": "integer"}
    assert schema["properties"]["obj"]["type"] == "object"
    assert schema["properties"]["obj"]["properties"] == {"x": {"type": "string"}}


def test_required_and_optional_parameters():
    parameters = [
        ToolParameter(name="required_param", type="string", required=True),
        ToolParameter(name="optional_param", type="string", required=False),
    ]

    schema = SchemaGenerator.generate(parameters)

    assert schema["required"] == ["required_param"]
    assert "optional_param" not in schema["required"]


def test_no_required_key_when_all_parameters_optional():
    parameters = [ToolParameter(name="x", type="string", required=False)]

    schema = SchemaGenerator.generate(parameters)

    assert "required" not in schema


def test_additional_properties_defaults_to_false():
    schema = SchemaGenerator.generate([ToolParameter(name="x", type="string")])
    assert schema["additionalProperties"] is False


def test_additional_properties_can_be_enabled():
    schema = SchemaGenerator.generate(
        [ToolParameter(name="x", type="string")], additional_properties=True
    )
    assert schema["additionalProperties"] is True


def test_array_defaults_items_to_string_when_not_specified():
    schema = SchemaGenerator.generate([ToolParameter(name="arr", type="array")])
    assert schema["properties"]["arr"]["items"] == {"type": "string"}


def test_description_included_when_present():
    schema = SchemaGenerator.generate(
        [ToolParameter(name="x", type="string", description="an x value")]
    )
    assert schema["properties"]["x"]["description"] == "an x value"
