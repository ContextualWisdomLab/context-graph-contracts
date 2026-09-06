"""Cross-field admission regressions for Context Assertion CloudEvents."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from cwl_context_contracts import (
    CanonicalAssetUri,
    CanonicalAuthorityUri,
    CloudEventEnvelope,
    ContextAssertion,
    load_fixture,
)
from cwl_context_contracts.assertion import (
    ASSERTION_DATA_SCHEMA,
    ASSERTION_EVENT_TYPE,
)
from tests.conftest import EVENT_UUID7_TEXT

_OTHER_UUID7 = "0195d145-64e8-7f4f-8a23-a0cc784cb799"


def _assertion() -> ContextAssertion:
    """Load one semantically conformant Context Assertion fixture."""

    return ContextAssertion.from_mapping(load_fixture("valid-assertion.json"))


def _assertion_with_truth_status(truth_status: str) -> ContextAssertion:
    """Return the fixture with one explicit producer-supplied truth disposition."""

    value = load_fixture("valid-assertion.json")
    value["truth_status"] = truth_status
    return ContextAssertion.from_mapping(value)


def _authoritative_assertion() -> ContextAssertion:
    """Return the fixture as owning-domain authoritative truth."""

    return _assertion_with_truth_status("authoritative")


def _source() -> CanonicalAuthorityUri:
    """Return the authoritative event source for the fixture tenant."""

    return CanonicalAuthorityUri.build(
        tenant_id="tenant_001",
        authority="lineage_weave",
    )


def _foreign_source() -> CanonicalAuthorityUri:
    """Return a same-tenant producer that does not own the fixture subject."""

    return CanonicalAuthorityUri.build(
        tenant_id="tenant_001",
        authority="wardnet",
    )


def _event(
    assertion: ContextAssertion,
    *,
    subject: CanonicalAssetUri | None = None,
    source: CanonicalAuthorityUri | None = None,
    event_type: str = ASSERTION_EVENT_TYPE,
    data_schema: str = ASSERTION_DATA_SCHEMA,
) -> CloudEventEnvelope:
    """Wrap one assertion with optionally hostile cross-field event identity."""

    return CloudEventEnvelope(
        event_id=UUID(EVENT_UUID7_TEXT),
        source=_source() if source is None else source,
        event_type=event_type,
        subject=assertion.subject if subject is None else subject,
        event_time=datetime(2026, 1, 15, 9, 6, tzinfo=UTC),
        data=assertion.to_mapping(),
        data_schema=data_schema,
        extensions={"tenantid": "tenant_001"},
    )


def test_context_assertion_event_admission_round_trips_exact_assertion() -> None:
    """The admission boundary returns the assertion bound by the event identity."""

    assertion = _assertion()
    assert ContextAssertion.from_event(_event(assertion)) == assertion


def test_context_assertion_event_rejects_non_event_input() -> None:
    """Callers cannot bypass the typed CloudEvent boundary with an arbitrary mapping."""

    with pytest.raises(TypeError, match="event must be a CloudEventEnvelope"):
        ContextAssertion.from_event({})  # type: ignore[arg-type]


def test_context_assertion_event_rejects_subject_data_identity_mismatch() -> None:
    """A same-tenant routing subject cannot point at a different assertion subject."""

    assertion = _assertion()
    other_subject = CanonicalAssetUri.build(
        tenant_id="tenant_001",
        authority="lineage_weave",
        object_type="source_record",
        object_id=_OTHER_UUID7,
    )
    with pytest.raises(ValueError, match="event subject must equal assertion subject"):
        ContextAssertion.from_event(_event(assertion, subject=other_subject))


def test_authoritative_assertion_requires_owning_domain_event_source() -> None:
    """A foreign producer cannot label another authority's subject as authoritative."""

    assertion = _authoritative_assertion()
    foreign_source = _foreign_source()

    with pytest.raises(
        ValueError,
        match="authoritative assertion source must own the assertion subject",
    ):
        assertion.into_event(
            event_id=UUID(EVENT_UUID7_TEXT),
            source=foreign_source,
            event_time=datetime(2026, 1, 15, 9, 6, tzinfo=UTC),
        )

    hostile_event = _event(assertion, source=foreign_source)
    with pytest.raises(
        ValueError,
        match="authoritative assertion source must own the assertion subject",
    ):
        ContextAssertion.from_event(hostile_event)


@pytest.mark.parametrize("truth_status", ["superseded", "rejected"])
def test_owner_controlled_disposition_requires_owning_domain_event_source(
    truth_status: str,
) -> None:
    """Foreign producers cannot supersede or reject another domain's assertion."""

    assertion = _assertion_with_truth_status(truth_status)
    foreign_source = _foreign_source()

    with pytest.raises(
        ValueError,
        match="owner-controlled assertion source must own the assertion subject",
    ):
        assertion.into_event(
            event_id=UUID(EVENT_UUID7_TEXT),
            source=foreign_source,
            event_time=datetime(2026, 1, 15, 9, 6, tzinfo=UTC),
        )

    hostile_event = _event(assertion, source=foreign_source)
    with pytest.raises(
        ValueError,
        match="owner-controlled assertion source must own the assertion subject",
    ):
        ContextAssertion.from_event(hostile_event)


def test_observed_assertion_can_retain_foreign_observer_source() -> None:
    """Observer identity remains explicit without promoting the observation to truth."""

    assertion = _assertion()
    event = _event(assertion, source=_foreign_source())
    assert ContextAssertion.from_event(event) == assertion


@pytest.mark.parametrize(
    ("event_type", "data_schema", "message"),
    [
        (
            "org.contextualwisdomlab.context_graph.other.v1",
            ASSERTION_DATA_SCHEMA,
            "event type",
        ),
        (
            ASSERTION_EVENT_TYPE,
            "https://schemas.contextualwisdomlab.org/context/other.v1.schema.json",
            "dataschema",
        ),
    ],
)
def test_context_assertion_event_rejects_wrong_contract_identity(
    event_type: str,
    data_schema: str,
    message: str,
) -> None:
    """Event type and dataschema cannot drift from the published assertion contract."""

    assertion = _assertion()
    with pytest.raises(ValueError, match=message):
        ContextAssertion.from_event(
            _event(
                assertion,
                event_type=event_type,
                data_schema=data_schema,
            )
        )
