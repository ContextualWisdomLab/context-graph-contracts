"""Packaged JSON Schema conformance tests."""

import json
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from cwl_context_contracts import available_schema_names, load_schema
from tests.conftest import RFC3339_FORMAT_CHECKER, UUID7_TEXT


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
        format_checker=RFC3339_FORMAT_CHECKER,
    )
    fixture_root = files("tests.fixtures")
    valid = json.loads(fixture_root.joinpath("valid-event.json").read_text())
    invalid = json.loads(fixture_root.joinpath("invalid-event.json").read_text())
    assert list(validator.iter_errors(valid)) == []
    assert list(validator.iter_errors(invalid))

    assertion_validator = Draft202012Validator(
        load_schema("context-assertion.schema.json"),
        registry=registry,
        format_checker=RFC3339_FORMAT_CHECKER,
    )
    valid_assertion = json.loads(
        fixture_root.joinpath("valid-assertion.json").read_text()
    )
    invalid_assertion = json.loads(
        fixture_root.joinpath("invalid-assertion.json").read_text()
    )
    assert list(assertion_validator.iter_errors(valid_assertion)) == []
    assert list(assertion_validator.iter_errors(invalid_assertion))


@pytest.mark.parametrize("field_name", ["valid_to", "superseded_at"])
def test_bitemporal_schema_rejects_explicit_null_open_end(field_name: str) -> None:
    """Canonical v1 open intervals omit end members rather than encoding null."""

    validator = Draft202012Validator(
        load_schema("bitemporal-interval.schema.json"),
        format_checker=RFC3339_FORMAT_CHECKER,
    )
    open_interval = {
        "valid_from": "2026-01-15T09:00:00Z",
        "recorded_at": "2026-01-15T09:05:00Z",
    }
    assert list(validator.iter_errors(open_interval)) == []
    hostile = {**open_interval, field_name: None}
    assert list(validator.iter_errors(hostile))


@pytest.mark.parametrize(
    ("schema_name", "valid_value", "invalid_value"),
    [
        (
            "canonical-authority-uri.schema.json",
            "urn:cwl:tenant_001:ea_core",
            "urn:cwl:tenant__001:ea_core",
        ),
        (
            "canonical-authority-uri.schema.json",
            "urn:cwl:tenant_001:ea_core",
            "urn:cwl:t_enant:ea_core",
        ),
        (
            "canonical-asset-uri.schema.json",
            f"urn:cwl:tenant_001:ea_core:application_record:{UUID7_TEXT}",
            f"urn:cwl:tenant_001:ea__core:application_record:{UUID7_TEXT}",
        ),
        (
            "canonical-asset-uri.schema.json",
            f"urn:cwl:tenant_001:ea_core:application_record:{UUID7_TEXT}",
            f"urn:cwl:tenant_001:ea_core:application_record_:{UUID7_TEXT}",
        ),
    ],
)
def test_uri_schemas_enforce_canonical_lower_snake_segments(
    schema_name: str,
    valid_value: str,
    invalid_value: str,
) -> None:
    """Packaged schemas accept one spelling for every lower-snake segment."""
    validator = Draft202012Validator(load_schema(schema_name))
    assert list(validator.iter_errors(valid_value)) == []
    assert list(validator.iter_errors(invalid_value))


def test_unknown_schema_name_fails_closed() -> None:
    """Callers cannot read arbitrary package resources."""

    with pytest.raises(ValueError, match="unknown schema"):
        load_schema("../pyproject.toml")
