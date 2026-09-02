"""Executable conformance evidence for ADR-0016's org-hierarchy membership.

Closes the four gaps raised when PR #23 (originally ADR-0001, now ADR-0016)
was reviewed and closed: wire-interpretation ambiguity between ADR-0006's
cross-classification ``memberships[]`` reading and this ADR's ancestor-
closure reading, bitemporal/replay semantics, primary-membership
cardinality, and reproducibility (Deferred item 5 in the ADR is implemented
here, not deferred).
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from cwl_context_contracts import (
    BitemporalInterval,
    CanonicalAssetUri,
    ContextAssertion,
    ContextMembership,
    ProvenanceReference,
    TruthStatus,
    available_conformance_profile_names,
    available_schema_names,
    load_conformance_profile,
    load_schema,
)

_ORG_HIERARCHY_PROFILE = "org-hierarchy-membership-semantics.v1.json"
_ORG_MEMBER_PREDICATES = frozenset(
    {"org_member_primary", "org_member_secondary", "org_member_observed"}
)
_DIGEST = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def assert_ancestor_closure_chain(assertion: ContextAssertion) -> None:
    """Reject a ``memberships[]`` that is not one unbroken ancestor chain.

    ADR-0016 reuses ``ContextMembership.memberships[]`` to mean a
    positional, denormalized ancestor-closure list. ADR-0006 already uses
    the identical array shape to mean unrelated cross-classification
    memberships. Neither ``context-assertion.schema.json`` nor
    ``ContextAssertion.__post_init__`` can tell the two readings apart --
    this is the predicate-conditioned convention check that does, without
    editing the shared schema owned by still-unmerged PR #4.
    """
    if assertion.predicate not in _ORG_MEMBER_PREDICATES:
        return
    memberships = assertion.memberships
    # Deliberately non-strict: adjacent pairs over N items yield N-1 pairs.
    for earlier, later in zip(memberships, memberships[1:], strict=False):
        if earlier.membership_level <= later.membership_level:
            raise ValueError(
                "org_member_* memberships must be ordered by strictly "
                "descending membership_level (leaf first, root last)"
            )
        if earlier.parent_context_ref != later.context_ref:
            raise ValueError(
                "org_member_* memberships must form one unbroken ancestor "
                "chain: each entry's parent_context_ref must equal the "
                "next entry's context_ref"
            )
    if memberships[-1].parent_context_ref is not None:
        raise ValueError(
            "org_member_* memberships must terminate at a root entry "
            "whose parent_context_ref is null"
        )


def assert_single_primary_membership_per_subject(
    assertions: Sequence[ContextAssertion],
) -> None:
    """Reject two overlapping ``org_member_primary`` assertions per subject.

    Nothing in ``context-assertion.schema.json`` or ``ContextAssertion``
    enforces this -- ``predicate`` is validated only by a generic
    lowercase-snake pattern (ADR-0016's own Risks section names this gap
    explicitly). This is the executable cardinality guard a consumer runs
    across a subject's assertion history before treating one
    ``org_member_primary`` as authoritative.
    """
    by_subject: dict[str, list[ContextAssertion]] = defaultdict(list)
    for assertion in assertions:
        if assertion.predicate == "org_member_primary":
            by_subject[str(assertion.subject)].append(assertion)
    for subject, primaries in by_subject.items():
        ordered = sorted(primaries, key=lambda item: item.interval.valid_from)
        # Deliberately non-strict: adjacent pairs over N items yield N-1 pairs.
        for earlier, later in zip(ordered, ordered[1:], strict=False):
            earlier_end = earlier.interval.valid_to
            if earlier_end is None or earlier_end > later.interval.valid_from:
                raise ValueError(
                    f"subject {subject!r} has overlapping org_member_primary "
                    "assertions: primary membership must be single-valued "
                    "at any instant"
                )


def _schema_registry() -> Registry:
    """Return every packaged schema as one Draft 2020-12 registry."""
    schemas = [load_schema(name) for name in available_schema_names()]
    return Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )


def _assertion_validator() -> Draft202012Validator:
    """Return a Draft 2020-12 validator for ``context-assertion.schema.json``."""
    return Draft202012Validator(
        load_schema("context-assertion.schema.json"),
        registry=_schema_registry(),
    )


def _load_fixture(name: str) -> dict[str, object]:
    """Load one org-hierarchy fixture from ``tests/fixtures``."""
    text = files("tests.fixtures").joinpath(name).read_text()
    return json.loads(text)


def _tenant_010_unit(object_type: str, tail: str) -> CanonicalAssetUri:
    """Build a ``tenant_010`` asset URI with a fixture-scoped UUIDv7 tail."""
    return CanonicalAssetUri.build(
        tenant_id="tenant_010",
        authority="orgmetra",
        object_type=object_type,
        object_id=f"0195d145-64e8-7f4f-8a23-a0cc784cb{tail}",
    )


def _interval(start: datetime, end: datetime | None = None) -> BitemporalInterval:
    """Return an interval recorded five minutes after it starts validity."""
    return BitemporalInterval(
        valid_from=start,
        recorded_at=start + timedelta(minutes=5),
        valid_to=end,
    )


def _org_assertion(
    *,
    assertion_tail: str,
    subject_tail: str,
    object_tail: str,
    memberships: tuple[ContextMembership, ...],
    interval: BitemporalInterval,
    predicate: str = "org_member_primary",
) -> ContextAssertion:
    """Build one org-hierarchy assertion for the tests below."""
    return ContextAssertion(
        assertion_id=f"0195d145-64e8-7f4f-8a23-a0cc784cb{assertion_tail}",
        subject=_tenant_010_unit("person", subject_tail),
        predicate=predicate,
        object=_tenant_010_unit("organization_unit", object_tail),
        truth_status=TruthStatus.AUTHORITATIVE,
        interval=interval,
        memberships=memberships,
        provenance=ProvenanceReference(
            _tenant_010_unit("assignment_record", "804"),
            _DIGEST,
            "$.assignments[0]",
        ),
    )


# --- (e) Reproducibility: fixtures and a packaged conformance profile ---


def test_org_hierarchy_conformance_profile_is_packaged_and_loadable() -> None:
    """Deferred item 5 (conformance fixtures) is shipped, not merely promised."""
    assert _ORG_HIERARCHY_PROFILE in available_conformance_profile_names()
    profile = load_conformance_profile(_ORG_HIERARCHY_PROFILE)
    assert profile["invalid_vectors"]


def test_valid_and_invalid_org_membership_fixtures_validate_against_schema() -> None:
    """``tests/fixtures/{valid,invalid}-org-membership.json`` are real vectors."""
    validator = _assertion_validator()
    valid = _load_fixture("valid-org-membership.json")
    invalid = _load_fixture("invalid-org-membership.json")
    assert list(validator.iter_errors(valid)) == []
    assert list(validator.iter_errors(invalid))


def test_valid_org_membership_fixture_round_trips_and_satisfies_chain_check() -> None:
    """The valid fixture parses and passes the ancestor-closure chain check."""
    fixture = _load_fixture("valid-org-membership.json")
    assertion = ContextAssertion.from_mapping(fixture)
    assert assertion.predicate == "org_member_primary"
    assert_ancestor_closure_chain(assertion)  # does not raise


def test_invalid_org_membership_fixture_is_rejected_by_context_assertion_too() -> None:
    """The invalid fixture fails ``from_mapping``, not just the schema."""
    with pytest.raises(ValueError, match="provenance"):
        ContextAssertion.from_mapping(_load_fixture("invalid-org-membership.json"))


# --- (b) Wire-interpretation ambiguity ---


def test_packaged_invalid_vectors_are_schema_valid_but_chain_invalid() -> None:
    """Packaged invalid vectors pass the schema and ``ContextAssertion``.

    Only the new ``assert_ancestor_closure_chain`` check catches them.
    """
    profile = load_conformance_profile(_ORG_HIERARCHY_PROFILE)
    validator = _assertion_validator()
    for vector in profile["invalid_vectors"]:
        value = vector["value"]
        assert list(validator.iter_errors(value)) == []
        assertion = ContextAssertion.from_mapping(value)  # does not raise either
        with pytest.raises(ValueError, match=vector["error_pattern"]):
            assert_ancestor_closure_chain(assertion)


def test_schema_alone_cannot_discriminate_membership_interpretation() -> None:
    """An ADR-0006-shaped cross-classification array also validates as org_member_*."""
    cross_classification = (
        ContextMembership(
            context_ref=_tenant_010_unit("analysis_run", "820"),
            membership_level=1,
            parent_context_ref=_tenant_010_unit("workspace_record", "821"),
        ),
        ContextMembership(
            context_ref=_tenant_010_unit("employment_group", "822"),
            membership_level=0,
            parent_context_ref=None,
        ),
    )
    reinterpreted = _org_assertion(
        assertion_tail="823",
        subject_tail="802",
        object_tail="820",
        memberships=cross_classification,
        interval=_interval(datetime(2026, 1, 1, tzinfo=UTC)),
    )
    validator = _assertion_validator()
    # The same schema accepts this ADR-0006-shaped array under org_member_primary.
    assert list(validator.iter_errors(reinterpreted.to_mapping())) == []
    # Only the predicate-conditioned convention check tells the two readings apart.
    with pytest.raises(ValueError, match="unbroken ancestor chain"):
        assert_ancestor_closure_chain(reinterpreted)


# --- (e) Verification section, committed as tests instead of a scratch script ---


def test_two_independent_tenant_roots_both_validate() -> None:
    """Two null-parent roots coexist in one tenant -- verification case 1."""
    validator = _assertion_validator()
    for assertion_tail, subject_tail, object_tail in (
        ("832", "833", "830"),
        ("834", "835", "831"),
    ):
        root_chain = (
            ContextMembership(
                context_ref=_tenant_010_unit("organization_unit", object_tail),
                membership_level=0,
                parent_context_ref=None,
            ),
        )
        assertion = _org_assertion(
            assertion_tail=assertion_tail,
            subject_tail=subject_tail,
            object_tail=object_tail,
            memberships=root_chain,
            interval=_interval(datetime(2026, 1, 1, tzinfo=UTC)),
        )
        assert list(validator.iter_errors(assertion.to_mapping())) == []
        assert_ancestor_closure_chain(assertion)  # does not raise


def test_reversed_regional_hq_business_division_direction_validates() -> None:
    """Parent-child direction between two type labels can invert -- case 2."""
    normal_direction = (
        ContextMembership(
            context_ref=_tenant_010_unit("affiliate", "840"),
            membership_level=1,
            parent_context_ref=_tenant_010_unit("regional_hq", "841"),
        ),
        ContextMembership(
            context_ref=_tenant_010_unit("regional_hq", "841"),
            membership_level=0,
            parent_context_ref=None,
        ),
    )
    reversed_direction = (
        ContextMembership(
            context_ref=_tenant_010_unit("regional_hq", "842"),
            membership_level=1,
            parent_context_ref=_tenant_010_unit("business_division", "843"),
        ),
        ContextMembership(
            context_ref=_tenant_010_unit("business_division", "843"),
            membership_level=0,
            parent_context_ref=None,
        ),
    )
    validator = _assertion_validator()
    for tail, memberships in (("844", normal_direction), ("845", reversed_direction)):
        assertion = _org_assertion(
            assertion_tail=tail,
            subject_tail="846",
            object_tail=tail,
            memberships=memberships,
            interval=_interval(datetime(2026, 1, 1, tzinfo=UTC)),
        )
        assert list(validator.iter_errors(assertion.to_mapping())) == []
        assert_ancestor_closure_chain(assertion)  # does not raise


# --- (c) Bitemporal / replay semantics ---


def test_bitemporal_interval_has_no_covers_method() -> None:
    """Locks in the gap: ``is_valid_at``/``was_known_at`` are the real model."""
    interval = _interval(datetime(2026, 1, 1, tzinfo=UTC))
    assert not hasattr(interval, "covers")
    assert hasattr(interval, "is_valid_at")
    assert hasattr(interval, "was_known_at")


def test_replay_reconstructs_past_belief_via_was_known_at_not_is_valid_at() -> None:
    """A reparented ancestor's correction shows in ``was_known_at``, not validity."""
    real_world_start = datetime(2026, 1, 1, tzinfo=UTC)
    original_recorded_at = datetime(2026, 1, 1, 0, 5, tzinfo=UTC)
    correction_recorded_at = datetime(2026, 3, 1, tzinfo=UTC)
    audit_instant = datetime(2026, 2, 1, tzinfo=UTC)  # between the two recordings

    original = BitemporalInterval(
        valid_from=real_world_start,
        recorded_at=original_recorded_at,
        superseded_at=correction_recorded_at,
    )
    corrected = BitemporalInterval(
        valid_from=real_world_start,
        recorded_at=correction_recorded_at,
    )

    # Replay: "what did the system believe as of audit_instant?"
    assert original.was_known_at(audit_instant) is True
    assert corrected.was_known_at(audit_instant) is False

    # Real-world validity is a separate dimension and does not move with the correction.
    assert original.is_valid_at(audit_instant) is True
    assert corrected.is_valid_at(audit_instant) is True


def test_correcting_a_reparented_ancestor_requires_a_new_assertion() -> None:
    """``ContextAssertion`` is frozen: no partial-patch API for ``memberships[]``."""
    fixture = _load_fixture("valid-org-membership.json")
    assertion = ContextAssertion.from_mapping(fixture)
    with pytest.raises(FrozenInstanceError):
        assertion.memberships = ()  # type: ignore[misc]


# --- (d) Primary-membership cardinality ---


def test_org_member_primary_cardinality_rejects_overlapping_assertions() -> None:
    """Two concurrent ``org_member_primary`` assertions for one subject are rejected."""
    memberships = (
        ContextMembership(
            context_ref=_tenant_010_unit("organization_unit", "850"),
            membership_level=0,
            parent_context_ref=None,
        ),
    )
    first = _org_assertion(
        assertion_tail="851",
        subject_tail="852",
        object_tail="850",
        memberships=memberships,
        interval=_interval(
            datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 6, 1, tzinfo=UTC)
        ),
    )
    second = _org_assertion(
        assertion_tail="853",
        subject_tail="852",
        object_tail="850",
        memberships=memberships,
        interval=_interval(datetime(2026, 3, 1, tzinfo=UTC)),  # overlaps first
    )
    with pytest.raises(ValueError, match="overlapping org_member_primary"):
        assert_single_primary_membership_per_subject([first, second])


def test_org_member_primary_cardinality_allows_sequential_supersession() -> None:
    """A later, non-overlapping ``org_member_primary`` is a legitimate correction."""
    memberships = (
        ContextMembership(
            context_ref=_tenant_010_unit("organization_unit", "850"),
            membership_level=0,
            parent_context_ref=None,
        ),
    )
    first = _org_assertion(
        assertion_tail="854",
        subject_tail="855",
        object_tail="850",
        memberships=memberships,
        interval=_interval(
            datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 6, 1, tzinfo=UTC)
        ),
    )
    second = _org_assertion(
        assertion_tail="856",
        subject_tail="855",
        object_tail="850",
        memberships=memberships,
        interval=_interval(datetime(2026, 6, 1, tzinfo=UTC)),  # starts as first ends
    )
    assert_single_primary_membership_per_subject([first, second])  # does not raise


def test_org_member_primary_cardinality_ignores_concurrent_secondary() -> None:
    """A concurrent ``org_member_secondary`` for the same subject is not a violation."""
    memberships = (
        ContextMembership(
            context_ref=_tenant_010_unit("organization_unit", "850"),
            membership_level=0,
            parent_context_ref=None,
        ),
    )
    primary = _org_assertion(
        assertion_tail="857",
        subject_tail="858",
        object_tail="850",
        memberships=memberships,
        interval=_interval(datetime(2026, 1, 1, tzinfo=UTC)),
    )
    secondary = _org_assertion(
        assertion_tail="859",
        subject_tail="858",
        object_tail="850",
        memberships=memberships,
        interval=_interval(datetime(2026, 1, 1, tzinfo=UTC)),
        predicate="org_member_secondary",
    )
    assert_single_primary_membership_per_subject([primary, secondary])  # does not raise
