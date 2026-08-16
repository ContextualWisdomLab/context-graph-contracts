"""CloudEvents envelope tests."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from cwl_context_contracts import CloudEventEnvelope
from tests.conftest import EVENT_UUID7_TEXT

EVENT_ID = UUID(EVENT_UUID7_TEXT)


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
        ({"time": "not-time"}, "parseable"),
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
    base = CloudEventEnvelope(
        event_id=EVENT_ID,
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data={},
    ).to_mapping()
    base.update(change)
    with pytest.raises(ValueError, match=message):
        CloudEventEnvelope.from_mapping(base)


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
