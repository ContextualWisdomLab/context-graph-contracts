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
    valid_case_ids = {vector["case_id"] for vector in profile["valid_vectors"]}
    assert valid_case_ids >= {
        "canonical_assertion_event",
        "foreign_observer_source_is_preserved",
        "foreign_inferred_source_is_preserved",
        "foreign_proposed_source_is_preserved",
    }
    invalid_case_ids = {vector["case_id"] for vector in profile["invalid_vectors"]}
    assert invalid_case_ids >= {
        "missing_event_id",
        "missing_event_source",
        "missing_event_subject",
        "missing_event_time",
        "missing_assertion_provenance",
        "wrong_event_datacontenttype",
        "event_subject_differs_from_assertion_subject",
        "wrong_assertion_event_type",
        "wrong_assertion_dataschema",
        "authoritative_assertion_from_foreign_source",
        "superseded_assertion_from_foreign_source",
        "rejected_assertion_from_foreign_source",
    }
    normative_requirement = profile["normative_requirement"]
    for truth_status in (
        "authoritative",
        "superseded",
        "rejected",
        "observed",
        "inferred",
        "proposed",
    ):
        assert truth_status in normative_requirement
    report = run_packaged_conformance()
    assert report.passed is True
