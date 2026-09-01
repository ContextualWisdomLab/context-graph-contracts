"""Packaged semantic-profile regressions for Context Assertion events."""

from cwl_context_contracts import (
    available_conformance_profile_names,
    load_conformance_profile,
    run_packaged_conformance,
)

_PROFILE_NAME = "context-assertion-event-semantics.v1.json"
_PROFILE_ID = "urn:cwl:context-contracts:context-assertion-event-semantics:v1"


def test_assertion_event_profile_is_packaged_and_executable() -> None:
    """Non-Python consumers receive executable cross-field event semantics."""

    assert _PROFILE_NAME in available_conformance_profile_names()
    profile = load_conformance_profile(_PROFILE_NAME)
    assert profile["profile_id"] == _PROFILE_ID
    assert {vector["case_id"] for vector in profile["invalid_vectors"]} >= {
        "missing_event_id",
        "wrong_event_datacontenttype",
        "event_subject_differs_from_assertion_subject",
        "wrong_assertion_event_type",
        "wrong_assertion_dataschema",
    }
    report = run_packaged_conformance()
    assert report.passed is True
