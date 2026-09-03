"""Structured-message admission regressions for Context Assertion events."""

import pytest

from cwl_context_contracts import (
    CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE,
    ContextAssertion,
    admit_context_assertion_message,
    load_conformance_profile,
    load_contract,
)

_PROFILE_NAME = "context-assertion-event-semantics.v1.json"


def _canonical_event() -> dict[str, object]:
    """Return the packaged canonical Context Assertion structured event."""

    profile = load_conformance_profile(_PROFILE_NAME)
    return profile["valid_vectors"][0]["value"]


def test_admission_media_type_matches_asyncapi_message_contract() -> None:
    """Bind executable admission to the media type advertised by AsyncAPI."""

    document = load_contract("context-fabric.asyncapi.json")
    advertised = document["components"]["messages"]["ContextAssertionEvent"][
        "contentType"
    ]
    assert advertised == CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE

    admitted = admit_context_assertion_message(advertised, _canonical_event())
    assert isinstance(admitted, ContextAssertion)
    assert admitted.truth_status.value == "observed"


def test_admission_rejects_non_advertised_structured_media_type() -> None:
    """A correct event body is still rejected under the wrong outer media type."""

    with pytest.raises(
        ValueError,
        match="Context Assertion media type must be application/cloudevents\\+json",
    ):
        admit_context_assertion_message("application/json", _canonical_event())


def test_admission_rejects_non_string_media_type() -> None:
    """Do not coerce an untyped transport value into the admission contract."""

    with pytest.raises(TypeError, match="Context Assertion media type must be a string"):
        admit_context_assertion_message(1, _canonical_event())  # type: ignore[arg-type]
