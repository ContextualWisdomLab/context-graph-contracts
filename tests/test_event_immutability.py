"""Mutation-safety tests for validated CloudEvents envelopes."""

from datetime import UTC, datetime
from uuid import UUID

from cwl_context_contracts import CloudEventEnvelope
from tests.conftest import EVENT_UUID7_TEXT


def test_event_snapshots_mutable_data_and_extensions(
    authority_uri,
    asset_uri,
) -> None:
    """Caller mutations cannot change an envelope after validation."""
    data = {"nested": {"safe": True}, "items": ["one"]}
    extensions = {"tenantid": authority_uri.tenant_id}
    event = CloudEventEnvelope(
        event_id=UUID(EVENT_UUID7_TEXT),
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data=data,
        extensions=extensions,
    )

    data["nested"]["safe"] = False
    data["items"].append("two")
    extensions["tenantid"] = "tenant_002"

    mapping = event.to_mapping()
    assert mapping["data"] == {"nested": {"safe": True}, "items": ["one"]}
    assert mapping["tenantid"] == authority_uri.tenant_id


def test_serialized_mapping_cannot_mutate_event_state(
    authority_uri,
    asset_uri,
) -> None:
    """Mutating one serialized copy does not alter later serializations."""
    event = CloudEventEnvelope(
        event_id=UUID(EVENT_UUID7_TEXT),
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data={"nested": {"safe": True}, "items": ["one"]},
        extensions={"tenantid": authority_uri.tenant_id},
    )

    first = event.to_mapping()
    first["data"]["nested"]["safe"] = False
    first["data"]["items"].append("two")
    first["tenantid"] = "tenant_002"

    assert event.to_mapping()["data"] == {
        "nested": {"safe": True},
        "items": ["one"],
    }
    assert event.to_mapping()["tenantid"] == authority_uri.tenant_id
