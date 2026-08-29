from __future__ import annotations

import pytest

from aiohttp_autodocs.schema import (
    _fix_refs,
    extract_schema,
    is_pydantic_model,
)
from tests.conftest import SampleItem, SampleNested


def test_is_pydantic_model():
    assert is_pydantic_model(SampleItem) is True
    assert is_pydantic_model(dict) is False
    assert is_pydantic_model("not_a_model") is False
    assert is_pydantic_model(None) is False


def test_extract_schema_none():
    components: dict = {}
    assert extract_schema(None, components) is None
    assert components == {}


def test_extract_schema_dict():
    components: dict = {}
    raw_dict = {"type": "object", "properties": {"name": {"type": "string"}}}
    result = extract_schema(raw_dict, components)
    assert result == raw_dict
    # Verify deep copy
    assert result is not raw_dict
    assert components == {}


def test_extract_schema_pydantic_model():
    components: dict = {}
    result = extract_schema(SampleItem, components)
    assert result == {"$ref": "#/components/schemas/SampleItem"}
    assert "SampleItem" in components
    assert components["SampleItem"]["type"] == "object"
    assert "properties" in components["SampleItem"]
    assert "id" in components["SampleItem"]["properties"]
    assert "name" in components["SampleItem"]["properties"]


def test_extract_schema_nested_pydantic_model():
    components: dict = {}
    result = extract_schema(SampleNested, components)
    assert result == {"$ref": "#/components/schemas/SampleNested"}
    assert "SampleNested" in components
    assert "SampleItem" in components
    nested_schema = components["SampleNested"]
    assert nested_schema["properties"]["item"]["$ref"] == "#/components/schemas/SampleItem"


def test_extract_schema_invalid_type():
    components: dict = {}
    with pytest.raises(TypeError, match="Cannot extract schema from"):
        extract_schema(123, components)  # type: ignore[arg-type]


def test_fix_refs_rewriting():
    schema_with_defs = {
        "items": {"$ref": "#/$defs/ItemSchema"},
        "nested": [{"$ref": "#/$defs/OtherSchema"}],
        "plain": "value",
    }
    fixed = _fix_refs(schema_with_defs)
    assert fixed["items"]["$ref"] == "#/components/schemas/ItemSchema"
    assert fixed["nested"][0]["$ref"] == "#/components/schemas/OtherSchema"
    assert fixed["plain"] == "value"
