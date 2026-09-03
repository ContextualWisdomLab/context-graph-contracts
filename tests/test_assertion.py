"""Context assertion and membership contract tests."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from cwl_context_contracts import (
    BitemporalInterval,
    CanonicalAssetUri,
    CanonicalAuthorityUri,
    ContextAssertion,
    ContextMembership,
    ProvenanceReference,
    TruthStatus,
    load_fixture,
)
from cwl_context_contracts.assertion import (
    ASSERTION_DATA_SCHEMA,
    ASSERTION_EVENT_TYPE,
    PREDICATE_DERIVED_FROM,
    PREDICATE_REALIZED_BY,
)
from tests.conftest import EVENT_UUID7_TEXT, UUID7_TEXT

ASSERTION_UUID7 = "0195d145-64e8-7f4f-8a23-a0cc784cb701"
OBJECT_UUID7 = "0195d145-64e8-7f4f-8a23-a0cc784cb702"
CONTEXT_UUID7 = "0195d145-64e8-7f4f-8a23-a0cc784cb704"
PARENT_UUID7 = "0195d145-64e8-7f4f-8a23-a0cc784cb705"
ORG_UUID7 = "0195d145-64e8-7f4f-8a23-a0cc784cb706"
DIGEST = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def _asset(
    object_type: str,
    object_id: str,
    authority: str = "lineage_weave",
) -> CanonicalAssetUri:
    """Build one tenant-scoped asset URI for assertion tests."""
    return CanonicalAssetUri.build(
        tenant_id="tenant_001",
        authority=authority,
        object_type=object_type,
        object_id=object_id,
    )


def _interval() -> BitemporalInterval:
    """Return an open bitemporal interval used by assertion tests."""
    return BitemporalInterval(
        datetime(2026, 1, 15, 9, 0, tzinfo=UTC),
        datetime(2026, 1, 15, 9, 5, tzinfo=UTC),
    )


def _membership() -> ContextMembership:
    """Return the proximal analysis-run membership."""
    return ContextMembership(
        context_ref=_asset("analysis_run", CONTEXT_UUID7),
        membership_level=0,
        parent_context_ref=_asset("workspace_record", PARENT_UUID7),
    )


def _provenance() -> ProvenanceReference:
    """Return evidence for observed or authoritative assertions."""
    return ProvenanceReference(
        _asset("analysis_run", CONTEXT_UUID7),
        DIGEST,
        "$.records[0]",
    )


def _assertion(**overrides: object) -> ContextAssertion:
    """Build one valid observed assertion, applying optional field overrides."""
    values: dict[str, object] = {
        "assertion_id": UUID(ASSERTION_UUID7),
        "subject": _asset("source_record", UUID7_TEXT),
        "predicate": PREDICATE_DERIVED_FROM,
        "object": _asset("source_record", OBJECT_UUID7),
        "truth_status": TruthStatus.OBSERVED,
        "interval": _interval(),
        "memberships": (_membership(),),
        "provenance": _provenance(),
    }
    values.update(overrides)
    return ContextAssertion(**values)  # type: ignore[arg-type]


def test_packaged_assertion_fixture_round_trips() -> None:
    """The published positive fixture is the exact consumer interchange shape."""
    fixture = load_fixture("valid-assertion.json")
    parsed = ContextAssertion.from_mapping(fixture)
    assert parsed.to_mapping() == fixture
    assert parsed.truth_status is TruthStatus.OBSERVED
    assert len(parsed.memberships) == 2


def test_invalid_assertion_fixture_keeps_inferred_lineage_non_authoritative() -> None:
    """Authoritative wire payloads without evidence fail closed."""
    with pytest.raises(ValueError, match="provenance"):
        ContextAssertion.from_mapping(load_fixture("invalid-assertion.json"))


def test_inferred_lineage_edge_cannot_be_rewritten_by_adapter() -> None:
    """LineageWeave inferred edges retain their exact status at this boundary."""
    assertion = _assertion(truth_status=TruthStatus.INFERRED, provenance=None)
    assert assertion.retain_truth_status(TruthStatus.INFERRED) is TruthStatus.INFERRED
    with pytest.raises(ValueError, match="retain truth status"):
        assertion.retain_truth_status(TruthStatus.AUTHORITATIVE)
    with pytest.raises(ValueError, match="retain truth status"):
        assertion.retain_truth_status(TruthStatus.OBSERVED)


def test_proposed_ea_relationship_remains_proposed() -> None:
    """Enterprise-architecture proposals do not become approved facts here."""
    assertion = _assertion(
        predicate=PREDICATE_REALIZED_BY,
        truth_status=TruthStatus.PROPOSED,
        provenance=None,
        subject=_asset("capability_record", UUID7_TEXT, "ea_core"),
        object=_asset("application_record", OBJECT_UUID7, "ea_core"),
        memberships=(
            ContextMembership(
                context_ref=_asset("architecture_model", CONTEXT_UUID7, "ea_core"),
                membership_level=0,
            ),
        ),
    )
    assert assertion.truth_status is TruthStatus.PROPOSED
    with pytest.raises(ValueError, match="retain truth status"):
        assertion.retain_truth_status(TruthStatus.AUTHORITATIVE)


def test_cross_classified_memberships_prevent_single_group_collapse() -> None:
    """An assertion can belong to an analysis run and an employment group at once."""
    assertion = _assertion(
        memberships=(
            _membership(),
            ContextMembership(
                context_ref=_asset("employment_group", ORG_UUID7, "orgmetra"),
                membership_level=1,
            ),
        )
    )
    assert [item.membership_level for item in assertion.memberships] == [0, 1]
    assert assertion.memberships[1].parent_context_ref is None


def test_temporal_reconstruction_uses_exclusive_knowledge_cutoff() -> None:
    """Consumers can replay what was known before a later supersession."""
    start = datetime(2024, 1, 1, tzinfo=UTC)
    recorded = datetime(2024, 1, 2, tzinfo=UTC)
    ended = datetime(2025, 6, 1, tzinfo=UTC)
    assertion = _assertion(
        interval=BitemporalInterval(start, recorded, ended, ended),
        truth_status=TruthStatus.SUPERSEDED,
        provenance=None,
    )
    assert assertion.interval.is_valid_at(datetime(2025, 5, 31, tzinfo=UTC)) is True
    assert assertion.interval.is_valid_at(ended) is False
    assert assertion.interval.was_known_at(datetime(2025, 5, 31, tzinfo=UTC)) is True
    assert assertion.interval.was_known_at(ended) is False


def test_into_event_uses_published_assertion_event_contract() -> None:
    """The CloudEvent wrapper points consumers at the assertion schema."""
    assertion = _assertion()
    event = assertion.into_event(
        event_id=UUID(EVENT_UUID7_TEXT),
        source=CanonicalAuthorityUri.build(
            tenant_id="tenant_001",
            authority="lineage_weave",
        ),
        event_time=datetime(2026, 1, 15, 9, 6, tzinfo=UTC),
        extensions={"tenantid": "tenant_001"},
    )
    assert event.event_type == ASSERTION_EVENT_TYPE
    assert event.data_schema == ASSERTION_DATA_SCHEMA
    assert ContextAssertion.from_mapping(event.to_mapping()["data"]) == assertion


@pytest.mark.parametrize(
    ("overrides", "error", "message"),
    [
        (
            {
                "subject": (
                    "urn:cwl:tenant_001:lineage_weave:source_record:" + UUID7_TEXT
                )
            },
            TypeError,
            "subject",
        ),
        (
            {
                "object": (
                    "urn:cwl:tenant_001:lineage_weave:source_record:" + OBJECT_UUID7
                )
            },
            TypeError,
            "object",
        ),
        ({"predicate": "DerivedFrom"}, ValueError, "predicate"),
        ({"interval": {"valid_from": "2026-01-15T09:00:00Z"}}, TypeError, "interval"),
        ({"memberships": "analysis_run"}, TypeError, "memberships"),
        ({"memberships": 1}, TypeError, "memberships"),
        ({"memberships": ()}, ValueError, "at least one"),
        ({"memberships": (object(),)}, TypeError, "ContextMembership"),
        ({"provenance": object()}, TypeError, "ProvenanceReference"),
        ({"truth_status": 1}, TypeError, "truth_status"),
        ({"truth_status": "trusted"}, ValueError, "unknown truth status"),
    ],
)
def test_assertion_constructor_rejects_invalid_public_inputs(
    overrides: dict[str, object],
    error: type[Exception],
    message: str,
) -> None:
    """Direct construction fails with stable contract errors."""
    with pytest.raises(error, match=message):
        _assertion(**overrides)


def test_assertion_rejects_self_loop_and_cross_tenant_edges() -> None:
    """Interchange edges stay inside one tenant and name two distinct assets."""
    subject = _asset("source_record", UUID7_TEXT)
    with pytest.raises(ValueError, match="different assets"):
        _assertion(object=subject)
    with pytest.raises(ValueError, match="same tenant"):
        _assertion(
            object=CanonicalAssetUri.build(
                tenant_id="tenant_002",
                authority="lineage_weave",
                object_type="source_record",
                object_id=OBJECT_UUID7,
            )
        )


def test_assertion_rejects_foreign_membership_and_duplicate_contexts() -> None:
    """Memberships are unique and tenant-scoped."""
    foreign = ContextMembership(
        context_ref=CanonicalAssetUri.build(
            tenant_id="tenant_002",
            authority="lineage_weave",
            object_type="analysis_run",
            object_id=CONTEXT_UUID7,
        ),
        membership_level=0,
    )
    with pytest.raises(ValueError, match="subject tenant"):
        _assertion(memberships=(foreign,))
    with pytest.raises(ValueError, match="unique"):
        _assertion(memberships=(_membership(), _membership()))


def test_assertion_rejects_foreign_provenance_and_missing_required_evidence() -> None:
    """Observed facts need same-tenant evidence; inferred facts may omit it."""
    foreign = ProvenanceReference(
        CanonicalAssetUri.build(
            tenant_id="tenant_002",
            authority="lineage_weave",
            object_type="analysis_run",
            object_id=CONTEXT_UUID7,
        ),
        DIGEST,
    )
    with pytest.raises(ValueError, match="provenance must belong"):
        _assertion(provenance=foreign)
    with pytest.raises(ValueError, match="need provenance"):
        _assertion(provenance=None)
    inferred = _assertion(truth_status=TruthStatus.INFERRED, provenance=None)
    assert inferred.provenance is None


def test_assertion_rejects_more_than_sixteen_memberships() -> None:
    """The interchange payload stays bounded."""
    memberships = tuple(
        ContextMembership(
            context_ref=_asset(
                "analysis_run",
                f"0195d145-64e8-7f4f-8a23-a0cc784cb7{index:02x}",
            ),
            membership_level=0,
        )
        for index in range(17)
    )
    with pytest.raises(ValueError, match="16"):
        _assertion(memberships=memberships)


def test_from_mapping_snapshots_once_and_rejects_hostile_shapes() -> None:
    """Parser boundaries fail closed before nested interpretation."""
    with pytest.raises(TypeError, match="mapping"):
        ContextAssertion.from_mapping([])  # type: ignore[arg-type]
    valid = load_fixture("valid-assertion.json")
    with pytest.raises(ValueError, match="unknown assertion fields"):
        ContextAssertion.from_mapping({**valid, "extra": "no"})
    missing = dict(valid)
    del missing["predicate"]
    with pytest.raises(ValueError, match="missing required"):
        ContextAssertion.from_mapping(missing)
    with pytest.raises(TypeError, match="memberships"):
        ContextAssertion.from_mapping({**valid, "memberships": "nope"})


def test_membership_constructor_and_parser_boundaries() -> None:
    """Membership values reject lookalikes, bool levels, and cyclic parents."""
    context = _asset("analysis_run", CONTEXT_UUID7)
    with pytest.raises(TypeError, match="context_ref"):
        ContextMembership(
            context_ref=(
                "urn:cwl:tenant_001:lineage_weave:analysis_run:" + CONTEXT_UUID7
            ),
            membership_level=0,
        )  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="membership_level"):
        ContextMembership(context_ref=context, membership_level=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="between 0 and 15"):
        ContextMembership(context_ref=context, membership_level=16)
    with pytest.raises(TypeError, match="parent_context_ref"):
        ContextMembership(
            context_ref=context,
            membership_level=0,
            parent_context_ref="x",
        )  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="differ"):
        ContextMembership(
            context_ref=context,
            membership_level=0,
            parent_context_ref=context,
        )
    with pytest.raises(ValueError, match="same tenant"):
        ContextMembership(
            context_ref=context,
            membership_level=0,
            parent_context_ref=CanonicalAssetUri.build(
                tenant_id="tenant_002",
                authority="lineage_weave",
                object_type="workspace_record",
                object_id=PARENT_UUID7,
            ),
        )
    with pytest.raises(TypeError, match="mapping"):
        ContextMembership.from_mapping([])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unknown membership fields"):
        ContextMembership.from_mapping(
            {"context_ref": str(context), "membership_level": 0, "extra": 1}
        )
    with pytest.raises(ValueError, match="requires context_ref"):
        ContextMembership.from_mapping({"membership_level": 0})
