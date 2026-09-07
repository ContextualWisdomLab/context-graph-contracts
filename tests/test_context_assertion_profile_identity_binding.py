"""Fail-closed identity binding between packaged profiles and admission receipts."""

from __future__ import annotations

import pytest

import cwl_context_contracts.context_assertion_admission as admission_module
from cwl_context_contracts import load_conformance_profile


def _canonical_event() -> dict[str, object]:
    """Return one packaged valid Context Assertion CloudEvent."""

    profile = load_conformance_profile("context-assertion-event-semantics.v1.json")
    return profile["valid_vectors"][0]["value"]


@pytest.mark.parametrize(
    ("profile_name", "field", "replacement"),
    [
        (
            "context-assertion-event-semantics.v1.json",
            "profile_version",
            2,
        ),
        (
            "context-assertion-message-admission.v1.json",
            "profile_id",
            "urn:cwl:context-contracts:context-assertion-message-admission:v2",
        ),
        (
            "context-assertion-message-admission.v1.json",
            "profile_version",
            2,
        ),
        (
            "context-assertion-message-admission.v1.json",
            "event_profile_id",
            "urn:cwl:context-contracts:context-assertion-event-semantics:v2",
        ),
        (
            "context-assertion-message-admission.v1.json",
            "structured_media_type",
            "application/json",
        ),
    ],
)
def test_admission_rejects_packaged_profile_identity_drift(
    monkeypatch: pytest.MonkeyPatch,
    profile_name: str,
    field: str,
    replacement: object,
) -> None:
    """A receipt cannot claim version/media identity that packaged evidence contradicts."""

    original_load = load_conformance_profile

    def load_profile(name: str):
        profile = original_load(name)
        if name == profile_name:
            profile[field] = replacement
        return profile

    monkeypatch.setattr(
        admission_module,
        "load_conformance_profile",
        load_profile,
        raising=False,
    )
    validator = getattr(admission_module, "_validate_packaged_profile_identity", None)
    if validator is not None and hasattr(validator, "cache_clear"):
        validator.cache_clear()

    with pytest.raises(RuntimeError, match="packaged Context Assertion profile identity"):
        admission_module.admit_context_assertion_message(
            admission_module.CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE,
            _canonical_event(),
        )

    if validator is not None and hasattr(validator, "cache_clear"):
        validator.cache_clear()
