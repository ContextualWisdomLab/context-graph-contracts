"""Structured-message admission regressions for Context Assertion events."""

import pytest

from cwl_context_contracts import (
    CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE,
    ContextAssertion,
    ContextAssertionAdmission,
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
    assert isinstance(admitted, ContextAssertionAdmission)
    assert isinstance(admitted.assertion, ContextAssertion)
    assert admitted.assertion.truth_status.value == "observed"


@pytest.mark.parametrize(
    "media_type",
    [
        "application/cloudevents+json; charset=utf-8",
        'Application/CloudEvents+JSON; Charset="UTF-8"',
    ],
)
def test_admission_accepts_standard_structured_json_media_type_variants(
    media_type: str,
) -> None:
    """Honor CloudEvents HTTP structured-mode media type parameter semantics."""

    admitted = admit_context_assertion_message(media_type, _canonical_event())

    assert isinstance(admitted, ContextAssertionAdmission)
    assert admitted.assertion.truth_status.value == "observed"


def test_admission_rejects_oversized_structured_media_type() -> None:
    """Bound caller-controlled transport metadata before regular-expression admission."""

    oversized = CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE + (" " * 257)

    with pytest.raises(
        ValueError,
        match="Context Assertion media type must not exceed 256 characters",
    ):
        admit_context_assertion_message(oversized, _canonical_event())


@pytest.mark.parametrize(
    "media_type",
    [
        "application/json",
        "application/cloudevents+json; charset=iso-8859-1",
        "application/cloudevents+json; charset=utf-8; charset=utf-8",
        "application/cloudevents+json; profile=unexpected",
        "application/cloudevents+json\r\nX-CWL-Bypass: true",
        "\r\napplication/cloudevents+json",
        "application/cloudevents+json\r\n",
        "\vapplication/cloudevents+json",
        "application/cloudevents+json\f",
    ],
)
def test_admission_rejects_non_advertised_structured_media_type(
    media_type: str,
) -> None:
    """Reject mismatched, ambiguous, or hostile outer structured media types."""

    with pytest.raises(
        ValueError,
        match="Context Assertion media type must be application/cloudevents\\+json",
    ):
        admit_context_assertion_message(media_type, _canonical_event())


def test_admission_rejects_non_string_media_type() -> None:
    """Do not coerce an untyped transport value into the admission contract."""

    with pytest.raises(TypeError, match="Context Assertion media type must be a string"):
        admit_context_assertion_message(1, _canonical_event())  # type: ignore[arg-type]


def test_admission_retains_envelope_identity_for_projection_receipts() -> None:
    """Keep the admitted event identity alongside its validated assertion."""

    value = _canonical_event()
    admitted = admit_context_assertion_message(
        CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE,
        value,
    )

    assert admitted.envelope.to_mapping() == value
    assert admitted.assertion.truth_status.value == "observed"
    assert admitted.profile_id == "urn:cwl:context-contracts:context-assertion-event-semantics:v1"
    assert admitted.profile_version == 1
    assert admitted.admission_version == 1


def test_admission_receipt_rejects_forged_types_and_mismatched_assertion() -> None:
    """Do not let callers forge a receipt around unrelated event or assertion state."""

    admitted = admit_context_assertion_message(
        CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE,
        _canonical_event(),
    )

    with pytest.raises(TypeError, match="envelope must be a CloudEventEnvelope"):
        ContextAssertionAdmission(  # type: ignore[arg-type]
            envelope={},
            assertion=admitted.assertion,
        )

    with pytest.raises(TypeError, match="assertion must be a ContextAssertion"):
        ContextAssertionAdmission(  # type: ignore[arg-type]
            envelope=admitted.envelope,
            assertion={},
        )

    mismatched_mapping = admitted.assertion.to_mapping()
    mismatched_mapping["predicate"] = "depends_on"
    mismatched_assertion = ContextAssertion.from_mapping(mismatched_mapping)
    with pytest.raises(
        ValueError,
        match="assertion must match the admitted CloudEvent envelope",
    ):
        ContextAssertionAdmission(
            envelope=admitted.envelope,
            assertion=mismatched_assertion,
        )
