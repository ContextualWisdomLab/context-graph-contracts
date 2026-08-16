"""Packaged JSON Schema conformance tests."""

import json
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from cwl_context_contracts import available_schema_names, load_schema


def test_all_packaged_schemas_are_valid_draft_2020_12() -> None:
    """Every packaged schema validates against its declared metaschema."""

    for name in available_schema_names():
        Draft202012Validator.check_schema(load_schema(name))


def test_positive_and_negative_fixtures() -> None:
    """Fixtures provide executable interoperability evidence."""

    schemas = [load_schema(name) for name in available_schema_names()]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    event_schema = load_schema("cloudevent-envelope.schema.json")
    validator = Draft202012Validator(
        event_schema,
        registry=registry,
        format_checker=FormatChecker(),
    )
    fixture_root = files("tests.fixtures")
    valid = json.loads(fixture_root.joinpath("valid-event.json").read_text())
    invalid = json.loads(fixture_root.joinpath("invalid-event.json").read_text())
    assert list(validator.iter_errors(valid)) == []
    assert list(validator.iter_errors(invalid))


def test_unknown_schema_name_fails_closed() -> None:
    """Callers cannot read arbitrary package resources."""

    with pytest.raises(ValueError, match="unknown schema"):
        load_schema("../pyproject.toml")
