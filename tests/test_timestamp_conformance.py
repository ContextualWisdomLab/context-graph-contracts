"""Portable timestamp conformance contract tests."""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from cwl_context_contracts import (
    available_conformance_profile_names,
    available_schema_names,
    format_cwl_timestamp,
    load_conformance_profile,
    load_schema,
    parse_cwl_timestamp,
)

_PROFILE_NAME = "cwl-timestamp-profile.v1.json"


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

    assert (
        list(validator.iter_errors(structurally_valid_but_semantically_invalid)) == []
    )


def test_packaged_timestamp_profile_is_executable() -> None:
    """Run the provider-neutral timestamp vectors through the reference parser."""
    assert _PROFILE_NAME in available_conformance_profile_names()
    profile = load_conformance_profile(_PROFILE_NAME)
    assert profile["json_schema_role"] == "structural_and_lexical_only"
    assert profile["basis"].startswith("RFC 3339 syntax")

    for value in profile["valid_values"]:
        parse_cwl_timestamp(value)
    for value in profile["invalid_values"]:
        with pytest.raises(ValueError, match="CWL timestamp profile"):
            parse_cwl_timestamp(value)


def test_parser_rejects_24_hour_midnight_alias() -> None:
    """Reject ISO 8601's 24:00 alias because CWL permits only hours 00 through 23."""
    with pytest.raises(ValueError, match="CWL timestamp profile"):
        parse_cwl_timestamp("2026-01-01T24:00:00Z")


@pytest.mark.parametrize("offset_seconds", [30, -30])
def test_formatter_fails_closed_for_sub_minute_offsets(offset_seconds: int) -> None:
    """The formatter must never emit Python-only offset-second wire syntax."""
    value = datetime(
        2026,
        8,
        16,
        12,
        0,
        tzinfo=timezone(timedelta(seconds=offset_seconds)),
    )

    with pytest.raises(ValueError, match="whole-minute UTC offset"):
        format_cwl_timestamp(value)


@pytest.mark.parametrize(
    "zone",
    [UTC, timezone(timedelta(hours=9)), timezone(-timedelta(hours=3, minutes=30))],
)
def test_formatter_output_round_trips_through_profile_parser(zone) -> None:
    """Every emitted timestamp is accepted and preserves the represented instant."""
    value = datetime(2026, 8, 16, 12, 0, 0, 123456, tzinfo=zone)

    serialized = format_cwl_timestamp(value)
    parsed = parse_cwl_timestamp(serialized)

    assert parsed == value
    assert parsed.timestamp() == value.timestamp()
    assert (serialized.endswith("Z")) is (value.utcoffset() == timedelta(0))


def test_unknown_conformance_profile_fails_closed() -> None:
    """Callers cannot load arbitrary package resources as conformance profiles."""
    with pytest.raises(ValueError, match="unknown conformance profile"):
        load_conformance_profile("../pyproject.toml")
