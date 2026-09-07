"""Packaged semantic-profile regressions for Context Assertion messages."""

from cwl_context_contracts import (
    CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE,
    available_conformance_profile_names,
    load_conformance_profile,
    run_packaged_conformance,
)

_PROFILE_NAME = "context-assertion-event-semantics.v1.json"
_PROFILE_ID = "urn:cwl:context-contracts:context-assertion-event-semantics:v1"
_MESSAGE_PROFILE_NAME = "context-assertion-message-admission.v1.json"


def test_assertion_event_profile_is_packaged_and_executable() -> None:
    """Non-Python consumers receive executable transport and event semantics."""

    profile_names = available_conformance_profile_names()
    assert _PROFILE_NAME in profile_names
    assert _MESSAGE_PROFILE_NAME in profile_names

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
        "missing_event_specversion",
        "missing_event_id",
        "missing_event_source",
        "missing_event_type",
        "missing_event_subject",
        "missing_event_time",
        "missing_event_datacontenttype",
        "missing_event_dataschema",
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

    message_profile = load_conformance_profile(_MESSAGE_PROFILE_NAME)
    assert message_profile["event_profile_id"] == _PROFILE_ID
    assert (
        message_profile["structured_media_type"]
        == CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE
    )
    message_invalid_case_ids = {
        vector["case_id"] for vector in message_profile["invalid_vectors"]
    }
    assert message_invalid_case_ids >= {
        "wrong_structured_media_type",
        "unsupported_structured_charset",
        "ambiguous_structured_parameters",
        "injected_structured_header",
    }

    report = run_packaged_conformance()
    assert report.passed is True
