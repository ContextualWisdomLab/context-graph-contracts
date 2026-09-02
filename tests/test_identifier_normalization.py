"""Identifier normalization tests across public construction paths."""

from datetime import UTC, datetime
from uuid import UUID

from cwl_context_contracts import CanonicalAssetUri, CloudEventEnvelope
from tests.conftest import EVENT_UUID7_TEXT, UUID7_TEXT


def test_asset_direct_text_identifier_matches_builder() -> None:
    """Direct text UUIDv7 input stores the same UUID value as the builder."""
    direct = CanonicalAssetUri(
        tenant_id="tenant_001",
        authority="ea_core",
        object_type="application_record",
        object_id=UUID7_TEXT,  # type: ignore[arg-type]
    )
    built = CanonicalAssetUri.build(
        tenant_id="tenant_001",
        authority="ea_core",
        object_type="application_record",
        object_id=UUID7_TEXT,
    )

    assert direct == built
    assert hash(direct) == hash(built)
    assert isinstance(direct.object_id, UUID)


def test_event_direct_text_identifier_matches_parsed_event(
    authority_uri,
    asset_uri,
) -> None:
    """Direct text event IDs normalize to the parsed UUIDv7 representation."""
    direct = CloudEventEnvelope(
        event_id=EVENT_UUID7_TEXT,  # type: ignore[arg-type]
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data={"phase": "phase_out", "path": ["legacy", "target"]},
    )
    parsed = CloudEventEnvelope.from_mapping(direct.to_mapping())

    assert direct == parsed
    assert hash(direct) == hash(parsed)
    assert isinstance(direct.event_id, UUID)
