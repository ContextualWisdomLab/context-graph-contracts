"""Installed conformance-fixture resource regressions."""

import pytest

from cwl_context_contracts import (
    CloudEventEnvelope,
    ContextAssertion,
    available_fixture_names,
    load_fixture,
)


def test_packaged_fixture_corpus_is_complete_and_parseable() -> None:
    """Consumers can execute packaged positive and negative conformance cases."""
    assert available_fixture_names() == (
        "valid-event.json",
        "invalid-event.json",
        "valid-assertion.json",
        "invalid-assertion.json",
        "data-management-contract.valid.json",
        "data-management-assessment.valid.json",
    )
    valid_event = load_fixture("valid-event.json")
    invalid_event = load_fixture("invalid-event.json")

    assert CloudEventEnvelope.from_mapping(valid_event).to_mapping() == valid_event
    with pytest.raises(ValueError, match="UUIDv7|RFC 9562"):
        CloudEventEnvelope.from_mapping(invalid_event)
    valid_assertion = load_fixture("valid-assertion.json")
    invalid_assertion = load_fixture("invalid-assertion.json")
    assert ContextAssertion.from_mapping(valid_assertion).to_mapping() == (
        valid_assertion
    )
    with pytest.raises(ValueError, match="provenance"):
        ContextAssertion.from_mapping(invalid_assertion)


def test_fixture_loader_rejects_unknown_names() -> None:
    """Fixture resource access is constrained to the published corpus."""
    with pytest.raises(ValueError, match="unknown fixture name"):
        load_fixture("missing.json")
