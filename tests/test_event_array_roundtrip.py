"""Regression coverage for structured-event array round trips."""

from datetime import UTC, datetime
from uuid import UUID

from cwl_context_contracts import CloudEventEnvelope
from tests.conftest import EVENT_UUID7_TEXT


def test_from_mapping_round_trip_preserves_nested_arrays(
    authority_uri,
    asset_uri,
) -> None:
    """A validated wire mapping with arrays remains parseable and unchanged."""
    event = CloudEventEnvelope(
        event_id=UUID(EVENT_UUID7_TEXT),
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data={
            "items": [
                {"values": [1, 2, 3]},
                [True, None, {"nested": ["a", "b"]}],
            ]
        },
    )

    mapping = event.to_mapping()

    assert CloudEventEnvelope.from_mapping(mapping).to_mapping() == mapping
