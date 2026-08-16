"""Portable timestamp conformance contract tests."""

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from cwl_context_contracts import (
    available_conformance_profile_names,
    available_schema_names,
    load_conformance_profile,
    load_schema,
    parse_rfc3339_timestamp,
)

_PROFILE_NAME = "rfc3339-timestamp-profile.v1.json"


def _schema_registry() -> Registry:
    """Return a registry containing every packaged contract schema."""
    schemas = [load_schema(name) for name in available_schema_names()]
    return Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )


def test_default_draft_202012_format_annotation_is_not_semantic_validation() -> None:
    """Prove the default dialect alone accepts a calendar-impossible timestamp."""
    validator = Draft202012Validator(
        load_schema("bitemporal-interval.schema.json"),
        registry=_schema_registry(),
    )
    structurally_valid_but_semantically_invalid = {
        "valid_from": "2026-02-30T12:00:00Z",
        "recorded_at": "2026-08-16T12:00:00Z",
    }

    assert list(validator.iter_errors(structurally_valid_but_semantically_invalid)) == []


def test_packaged_timestamp_profile_is_executable() -> None:
    """Run the provider-neutral timestamp vectors through the reference parser."""
    assert available_conformance_profile_names() == (_PROFILE_NAME,)
    profile = load_conformance_profile(_PROFILE_NAME)
    assert profile["json_schema_role"] == "structural_and_lexical_only"

    for value in profile["valid_values"]:
        parse_rfc3339_timestamp(value)
    for value in profile["invalid_values"]:
        with pytest.raises(ValueError, match="RFC 3339 timestamp"):
            parse_rfc3339_timestamp(value)


def test_unknown_conformance_profile_fails_closed() -> None:
    """Callers cannot load arbitrary package resources as conformance profiles."""
    with pytest.raises(ValueError, match="unknown conformance profile"):
        load_conformance_profile("../pyproject.toml")
