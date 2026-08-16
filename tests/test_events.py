"""CloudEvents envelope tests."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from cwl_context_contracts import CanonicalAssetUri, CloudEventEnvelope
from tests.conftest import EVENT_UUID7_TEXT

EVENT_ID = UUID(EVENT_UUID7_TEXT)


def _event_mapping(authority_uri, asset_uri) -> dict[str, object]:
    """Return a minimal valid structured-event mapping."""
    return CloudEventEnvelope(
        event_id=EVENT_ID,
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data={},
    ).to_mapping()


def test_event_round_trip_preserves_core_and_extension_fields(
    authority_uri,
    asset_uri,
) -> None:
    """Structured JSON preserves dataschema and approved extension fields."""
    event = CloudEventEnvelope(
        event_id=EVENT_ID,
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data={"phase": "phase_out"},
        data_schema=(
            "https://schemas.contextualwisdomlab.org/ea/"
            "lifecycle-changed.v1.schema.json"
        ),
        extensions={"tenantid": "tenant_001", "correlationid": "corr_001"},
    )
    mapping = event.to_mapping()
    assert mapping["source"] == "urn:cwl:tenant_001:ea_core"
    assert mapping["time"] == "2026-08-16T00:00:00Z"
    assert mapping["dataschema"].endswith("lifecycle-changed.v1.schema.json")
    assert CloudEventEnvelope.from_mapping(mapping).to_mapping() == mapping


def test_event_omits_absent_dataschema(authority_uri, asset_uri) -> None:
    """An event without a data schema does not emit a null core attribute."""
    event = CloudEventEnvelope(
        event_id=EVENT_ID,
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data={},
    )
    assert "dataschema" not in event.to_mapping()


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"specversion": "0.3"}, "specversion"),
        ({"datacontenttype": "text/plain"}, "datacontenttype"),
        ({"id": "550e8400-e29b-41d4-a716-446655440000"}, "UUIDv7"),
        (
            {
                "source": (
                    "urn:cwl:tenant_001:ea_core:application_record:"
                    + EVENT_UUID7_TEXT
                )
            },
            "authority",
        ),
        ({"type": "bad"}, "event_type"),
        ({"time": "not-time"}, "RFC 3339"),
        ({"dataschema": "relative/schema.json"}, "dataschema"),
    ],
)
def test_event_mapping_rejects_invalid_attributes(
    authority_uri,
    asset_uri,
    change,
    message,
) -> None:
    """Malformed structured events fail closed."""
    mapping = _event_mapping(authority_uri, asset_uri)
    mapping.update(change)
    with pytest.raises(ValueError, match=message):
        CloudEventEnvelope.from_mapping(mapping)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("id", 1),
        ("source", 1),
        ("type", 1),
        ("subject", 1),
        ("time", 1),
        ("dataschema", 1),
    ],
)
def test_event_mapping_rejects_non_string_core_attributes(
    authority_uri,
    asset_uri,
    field_name,
    field_value,
) -> None:
    """Core string attributes are not silently coerced from other types."""
    mapping = _event_mapping(authority_uri, asset_uri)
    mapping[field_name] = field_value
    with pytest.raises(TypeError, match=field_name):
        CloudEventEnvelope.from_mapping(mapping)


def test_event_mapping_rejects_non_string_attribute_name(
    authority_uri,
    asset_uri,
) -> None:
    """The structured-event object cannot contain non-string attribute keys."""
    mapping = _event_mapping(authority_uri, asset_uri)
    mapping[1] = "invalid"  # type: ignore[index]
    with pytest.raises(TypeError, match="attribute names"):
        CloudEventEnvelope.from_mapping(mapping)


def test_event_mapping_reports_missing_attributes() -> None:
    """Missing required attributes are reported deterministically."""
    with pytest.raises(ValueError, match="missing required"):
        CloudEventEnvelope.from_mapping(
            {"specversion": "1.0", "datacontenttype": "application/json"}
        )


@pytest.mark.parametrize(
    ("extensions", "message"),
    [
        ({"type": "shadow"}, "extension name"),
        ({"dataschema": "https://example.com/schema"}, "extension name"),
        ({"bad_name": "value"}, "extension name"),
        ({"tenantid": ""}, "non-empty"),
        ({"tenantid": 1}, "non-empty"),
    ],
)
def test_event_rejects_invalid_extensions(
    authority_uri,
    asset_uri,
    extensions,
    message,
) -> None:
    """Extensions cannot shadow core attributes or carry non-string values."""
    with pytest.raises(ValueError, match=message):
        CloudEventEnvelope(
            event_id=EVENT_ID,
            source=authority_uri,
            event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
            subject=asset_uri,
            event_time=datetime(2026, 8, 16, tzinfo=UTC),
            data={},
            extensions=extensions,
        )


def test_event_rejects_non_string_extension_names(
    authority_uri,
    asset_uri,
) -> None:
    """Extension attribute names are strings before grammar checks."""
    with pytest.raises(TypeError, match="extension names"):
        CloudEventEnvelope(
            event_id=EVENT_ID,
            source=authority_uri,
            event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
            subject=asset_uri,
            event_time=datetime(2026, 8, 16, tzinfo=UTC),
            data={},
            extensions={1: "value"},  # type: ignore[dict-item]
        )


def test_event_rejects_cross_tenant_subject(authority_uri) -> None:
    """Producer and subject must remain inside one tenant boundary."""
    foreign_subject = CanonicalAssetUri.build(
        tenant_id="tenant_002",
        authority="ea_core",
        object_type="application_record",
        object_id="0195d145-64e8-7f4f-8a23-a0cc784cb712",
    )
    with pytest.raises(ValueError, match="tenant"):
        CloudEventEnvelope(
            event_id=EVENT_ID,
            source=authority_uri,
            event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
            subject=foreign_subject,
            event_time=datetime(2026, 8, 16, tzinfo=UTC),
            data={},
        )


def test_event_rejects_tenant_extension_mismatch(authority_uri, asset_uri) -> None:
    """A redundant tenant extension cannot contradict the source tenant."""
    with pytest.raises(ValueError, match="tenantid"):
        CloudEventEnvelope(
            event_id=EVENT_ID,
            source=authority_uri,
            event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
            subject=asset_uri,
            event_time=datetime(2026, 8, 16, tzinfo=UTC),
            data={},
            extensions={"tenantid": "tenant_002"},
        )


def test_event_rejects_naive_time_and_non_mapping_data(
    authority_uri,
    asset_uri,
) -> None:
    """Events require timezone-aware time and object-shaped data."""
    with pytest.raises(ValueError, match="event_time"):
        CloudEventEnvelope(
            EVENT_ID,
            authority_uri,
            "org.contextualwisdomlab.ea.lifecycle.changed.v1",
            asset_uri,
            datetime(2026, 8, 16),
            {},
        )
    with pytest.raises(TypeError, match="mapping"):
        CloudEventEnvelope(
            EVENT_ID,
            authority_uri,
            "org.contextualwisdomlab.ea.lifecycle.changed.v1",
            asset_uri,
            datetime(2026, 8, 16, tzinfo=UTC),
            [],  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "data",
    [
        {"created_at": datetime(2026, 8, 16, tzinfo=UTC)},
        {"score": float("nan")},
        {"score": float("inf")},
        {1: "non_string_key"},
        {"tuple_value": (1, 2)},
        {"nested": [object()]},
    ],
)
def test_event_rejects_non_json_data(authority_uri, asset_uri, data) -> None:
    """Structured JSON events reject values that cannot cross the wire."""
    with pytest.raises((TypeError, ValueError), match="JSON"):
        CloudEventEnvelope(
            event_id=EVENT_ID,
            source=authority_uri,
            event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
            subject=asset_uri,
            event_time=datetime(2026, 8, 16, tzinfo=UTC),
            data=data,
        )


def test_event_rejects_cyclic_json_container(authority_uri, asset_uri) -> None:
    """Structured events reject cyclic containers rather than recursing."""
    cyclic: dict[str, object] = {}
    cyclic["self"] = cyclic
    with pytest.raises(ValueError, match="cycle"):
        CloudEventEnvelope(
            event_id=EVENT_ID,
            source=authority_uri,
            event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
            subject=asset_uri,
            event_time=datetime(2026, 8, 16, tzinfo=UTC),
            data=cyclic,
        )


def test_event_rejects_cyclic_json_list(authority_uri, asset_uri) -> None:
    """Structured events reject cyclic JSON arrays."""
    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(ValueError, match="cycle"):
        CloudEventEnvelope(
            event_id=EVENT_ID,
            source=authority_uri,
            event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
            subject=asset_uri,
            event_time=datetime(2026, 8, 16, tzinfo=UTC),
            data={"array": cyclic},
        )


def test_event_rejects_excessive_json_depth(authority_uri, asset_uri) -> None:
    """Structured events bound recursive validation depth."""
    nested: dict[str, object] = {}
    cursor = nested
    for _ in range(65):
        child: dict[str, object] = {}
        cursor["child"] = child
        cursor = child
    with pytest.raises(ValueError, match="depth"):
        CloudEventEnvelope(
            event_id=EVENT_ID,
            source=authority_uri,
            event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
            subject=asset_uri,
            event_time=datetime(2026, 8, 16, tzinfo=UTC),
            data=nested,
        )


def test_event_accepts_json_native_nested_data(authority_uri, asset_uri) -> None:
    """Structured JSON events accept every native JSON value category."""
    event = CloudEventEnvelope(
        event_id=EVENT_ID,
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data={
            "null_value": None,
            "boolean_value": True,
            "integer_value": 1,
            "number_value": 1.25,
            "array_value": ["item", 2, False],
            "object_value": {"status": "ok"},
        },
    )
    assert event.to_mapping()["data"]["object_value"] == {"status": "ok"}
