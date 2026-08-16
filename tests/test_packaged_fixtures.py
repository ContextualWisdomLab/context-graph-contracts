"""Installed conformance-fixture resource regressions."""

import pytest

from cwl_context_contracts import (
    CloudEventEnvelope,
    available_fixture_names,
    load_fixture,
)


def test_packaged_fixture_corpus_is_complete_and_parseable() -> None:
    """Consumers can execute positive and negative conformance cases from the package."""
    assert available_fixture_names() == ("valid-event.json", "invalid-event.json")
    valid_event = load_fixture("valid-event.json")
    invalid_event = load_fixture("invalid-event.json")

    assert CloudEventEnvelope.from_mapping(valid_event).to_mapping() == valid_event
    with pytest.raises(ValueError, match="UUIDv7|RFC 9562"):
        CloudEventEnvelope.from_mapping(invalid_event)


def test_fixture_loader_rejects_unknown_names() -> None:
    """Fixture resource access is constrained to the published corpus."""
    with pytest.raises(ValueError, match="unknown fixture name"):
        load_fixture("missing.json")
