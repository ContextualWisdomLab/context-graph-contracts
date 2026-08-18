"""Canonical UUIDv7 wire spelling must agree with published schemas."""

from __future__ import annotations

import pytest

from cwl_context_contracts import CloudEventEnvelope, ContextAssertion, load_fixture


@pytest.mark.parametrize(
    ("fixture_name", "identity_field", "parser"),
    [
        ("valid-assertion.json", "assertion_id", ContextAssertion.from_mapping),
        ("valid-event.json", "id", CloudEventEnvelope.from_mapping),
    ],
)
def test_wire_parsers_reject_uppercase_uuid7_text(
    fixture_name: str,
    identity_field: str,
    parser: object,
) -> None:
    """SDK parsing must not normalize wire UUID text rejected by JSON Schema."""

    fixture = load_fixture(fixture_name)
    original_identity = fixture[identity_field]
    assert isinstance(original_identity, str)
    uppercase_identity = original_identity.upper()
    assert uppercase_identity != original_identity

    hostile_payload = {**fixture, identity_field: uppercase_identity}
    with pytest.raises(ValueError, match="UUIDv7"):
        parser(hostile_payload)  # type: ignore[operator]
