"""Exact value-object equality tests for validated CloudEvents."""

from datetime import UTC, datetime
from uuid import UUID

from cwl_context_contracts import CloudEventEnvelope
from tests.conftest import EVENT_UUID7_TEXT


def _event(authority_uri, asset_uri, data) -> CloudEventEnvelope:
    """Build one event with stable identity and caller-selected JSON data."""
    return CloudEventEnvelope(
        event_id=UUID(EVENT_UUID7_TEXT),
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data=data,
        extensions={"correlationid": "corr_001"},
    )


def test_boolean_and_integer_payloads_are_distinct_values(
    authority_uri,
    asset_uri,
) -> None:
    """JSON boolean true never compares equal to JSON integer one."""
    boolean_event = _event(authority_uri, asset_uri, {"value": True})
    integer_event = _event(authority_uri, asset_uri, {"value": 1})

    assert boolean_event != integer_event
    assert hash(boolean_event) != hash(integer_event)


def test_integer_and_float_payloads_are_distinct_values(
    authority_uri,
    asset_uri,
) -> None:
    """JSON integer one never compares equal to JSON number 1.0."""
    integer_event = _event(authority_uri, asset_uri, {"value": 1})
    float_event = _event(authority_uri, asset_uri, {"value": 1.0})

    assert integer_event != float_event
    assert hash(integer_event) != hash(float_event)


def test_same_cloudevent_identity_with_different_payload_is_not_equal(
    authority_uri,
    asset_uri,
) -> None:
    """Full value equality exposes conflicting content under one source/id."""
    first = _event(authority_uri, asset_uri, {"phase": "active"})
    conflicting = _event(authority_uri, asset_uri, {"phase": "phase_out"})

    assert first != conflicting
    assert (first.source, first.event_id) == (conflicting.source, conflicting.event_id)


def test_mapping_insertion_order_does_not_change_event_value(
    authority_uri,
    asset_uri,
) -> None:
    """JSON object member order is not part of semantic event equality."""
    left = _event(authority_uri, asset_uri, {"a": 1, "b": [True, None]})
    right = _event(authority_uri, asset_uri, {"b": [True, None], "a": 1})

    assert left == right
    assert hash(left) == hash(right)
    assert left != object()
