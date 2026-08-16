"""Strict RFC 3339 regressions for CloudEvents timestamp handling."""

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from cwl_context_contracts import (
    CloudEventEnvelope,
    available_schema_names,
    load_schema,
)


_INVALID_RFC3339_TIMES = (
    "2026-08-16 12:00:00+00:00",
    "2026-W33-7T12:00:00+00:00",
    "2026-08-16T12:00:00+0000",
    "2026-08-16T12:00:00+00:00:30",
    "2026-08-16T12:00:00,123Z",
    "2026-02-30T12:00:00Z",
)


def _valid_mapping(authority_uri, asset_uri) -> dict[str, object]:
    """Return one valid event mapping suitable for timestamp mutation."""
    from datetime import UTC, datetime
    from uuid import UUID

    event = CloudEventEnvelope(
        event_id=UUID("0195d145-64e8-7f4f-8a23-a0cc784cb799"),
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, 12, 0, tzinfo=UTC),
        data={"phase": "phase_out"},
    )
    return event.to_mapping()


@pytest.mark.parametrize("timestamp", _INVALID_RFC3339_TIMES)
def test_event_parser_rejects_iso8601_forms_outside_rfc3339(
    authority_uri,
    asset_uri,
    timestamp: str,
) -> None:
    """Permissive ``datetime.fromisoformat`` forms must fail closed."""
    mapping = _valid_mapping(authority_uri, asset_uri)
    mapping["time"] = timestamp

    with pytest.raises(ValueError, match="RFC 3339"):
        CloudEventEnvelope.from_mapping(mapping)


@pytest.mark.parametrize(
    ("timestamp", "canonical"),
    [
        ("2026-08-16t12:00:00z", "2026-08-16T12:00:00Z"),
        (
            "2026-08-16T12:00:00.123456+09:00",
            "2026-08-16T12:00:00.123456+09:00",
        ),
    ],
)
def test_event_parser_accepts_rfc3339_case_and_fraction_forms(
    authority_uri,
    asset_uri,
    timestamp: str,
    canonical: str,
) -> None:
    """RFC 3339 timestamps parse and serialize to a stable canonical spelling."""
    mapping = _valid_mapping(authority_uri, asset_uri)
    mapping["time"] = timestamp

    parsed = CloudEventEnvelope.from_mapping(mapping)

    assert parsed.to_mapping()["time"] == canonical


@pytest.mark.parametrize("timestamp", _INVALID_RFC3339_TIMES)
def test_packaged_event_schema_rejects_non_rfc3339_time(timestamp: str) -> None:
    """The shipped schema gate enforces the same RFC 3339 timestamp boundary."""
    schemas = [load_schema(name) for name in available_schema_names()]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    validator = Draft202012Validator(
        load_schema("cloudevent-envelope.schema.json"),
        registry=registry,
        format_checker=FormatChecker(),
    )
    mapping = {
        "specversion": "1.0",
        "id": "0195d145-64e8-7f4f-8a23-a0cc784cb799",
        "source": "urn:cwl:tenant_001:ea_core",
        "type": "org.contextualwisdomlab.ea.lifecycle.changed.v1",
        "subject": (
            "urn:cwl:tenant_001:ea_core:application_record:"
            "0195d145-64e8-7f4f-8a23-a0cc784cb711"
        ),
        "time": timestamp,
        "datacontenttype": "application/json",
        "data": {},
    }

    assert list(validator.iter_errors(mapping))
