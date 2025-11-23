import pytest
from app.core.yaml_parser import YAMLParser, YAMLSyntaxError, MissingRequiredKeyError, InvalidSchemaError


def test_parse_valid_yaml():
    yaml_content = """
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
    parser = YAMLParser()
    schema = parser.parse_yaml(yaml_content)
    
    assert schema.contract_version == "1.0"
    assert schema.domain == "test"
    assert "user_id" in schema.schema
    assert schema.schema["user_id"].type == "string"


def test_parse_invalid_yaml_syntax():
    yaml_content = """
contract_version: "1.0
domain: test
"""
    parser = YAMLParser()
    
    with pytest.raises(YAMLSyntaxError):
        parser.parse_yaml(yaml_content)


def test_parse_missing_required_key():
    yaml_content = """
contract_version: "1.0"
domain: "test"
"""
    parser = YAMLParser()
    
    with pytest.raises(MissingRequiredKeyError):
        parser.parse_yaml(yaml_content)


def test_parse_invalid_field_type():
    yaml_content = """
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: invalid_type
    required: true
"""
    parser = YAMLParser()
    
    with pytest.raises(InvalidSchemaError):
        parser.parse_yaml(yaml_content)


def test_parse_nested_object():
    yaml_content = """
contract_version: "1.0"
domain: "test"
schema:
  user:
    type: object
    required: true
    properties:
      name:
        type: string
        required: true
      age:
        type: integer
        required: false
"""
    parser = YAMLParser()
    schema = parser.parse_yaml(yaml_content)
    
    assert "user" in schema.schema
    assert schema.schema["user"].type == "object"
    assert schema.schema["user"].properties is not None
    assert "name" in schema.schema["user"].properties


def test_parse_array_field():
    yaml_content = """
contract_version: "1.0"
domain: "test"
schema:
  tags:
    type: array
    required: true
    items:
      type: string
"""
    parser = YAMLParser()
    schema = parser.parse_yaml(yaml_content)
    
    assert "tags" in schema.schema
    assert schema.schema["tags"].type == "array"
    assert schema.schema["tags"].items is not None
    assert schema.schema["tags"].items.type == "string"


def test_serialize_to_yaml():
    yaml_content = """
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
    parser = YAMLParser()
    schema = parser.parse_yaml(yaml_content)
    
    serialized = parser.serialize_to_yaml(schema)
    
    assert "contract_version" in serialized
    assert "schema" in serialized
    assert "user_id" in serialized