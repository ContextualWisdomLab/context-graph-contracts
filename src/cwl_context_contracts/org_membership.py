"""Public semantic validators for organization-membership assertions."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations

from .assertion import ContextAssertion
from .temporal import BitemporalInterval

_ORG_MEMBER_PREDICATES = frozenset(
    {"org_member_primary", "org_member_secondary", "org_member_observed"}
)


def assert_ancestor_closure_chain(assertion: ContextAssertion) -> None:
    """Require an org-membership assertion to carry one complete ancestor chain.

    Organization predicates interpret ``memberships`` as a positional closure:
    the first item is the asserted leaf and each following item is its direct
    parent until the root. Levels therefore decrease by exactly one, parent
    references join adjacent entries, and the null-parent terminal root is
    always level zero. Non-organization predicates retain the generic
    cross-classification semantics of :class:`ContextMembership`.

    Args:
        assertion: Assertion whose organization-membership convention is checked.

    Raises:
        TypeError: If ``assertion`` is not a ``ContextAssertion``.
        ValueError: If an organization predicate does not contain a complete,
            direct ancestor closure ending at level-zero root.
    """
    if type(assertion) is not ContextAssertion:
        raise TypeError("assertion must be a ContextAssertion")
    if assertion.predicate not in _ORG_MEMBER_PREDICATES:
        return

    memberships = assertion.memberships
    for earlier, later in zip(memberships, memberships[1:], strict=False):
        if earlier.membership_level != later.membership_level + 1:
            raise ValueError(
                "org_member_* membership_level must decrease by exactly one "
                "between adjacent ancestor entries"
            )
        if earlier.parent_context_ref != later.context_ref:
            raise ValueError(
                "org_member_* memberships must form one unbroken ancestor "
                "chain: each entry's parent_context_ref must equal the next "
                "entry's context_ref"
            )

    root = memberships[-1]
    if root.parent_context_ref is not None:
        raise ValueError(
            "org_member_* memberships must terminate at a root entry whose "
            "parent_context_ref is null"
        )
    if root.membership_level != 0:
        raise ValueError("org_member_* root membership_level must be 0")


def _half_open_intervals_overlap(
    first_start: object,
    first_end: object | None,
    second_start: object,
    second_end: object | None,
) -> bool:
    """Return whether two already-validated half-open comparable intervals overlap."""
    return (first_end is None or second_start < first_end) and (
        second_end is None or first_start < second_end
    )


def _primary_intervals_conflict(
    first: BitemporalInterval,
    second: BitemporalInterval,
) -> bool:
    """Return whether two primary facts overlap in valid and recording time."""
    valid_overlap = _half_open_intervals_overlap(
        first.valid_from,
        first.valid_to,
        second.valid_from,
        second.valid_to,
    )
    recorded_overlap = _half_open_intervals_overlap(
        first.recorded_at,
        first.superseded_at,
        second.recorded_at,
        second.superseded_at,
    )
    return valid_overlap and recorded_overlap


def assert_single_primary_membership_per_subject(
    assertions: Sequence[ContextAssertion],
) -> None:
    """Reject simultaneously valid-and-known primary memberships for one subject.

    Primary uniqueness is bitemporal. Two historical assertions may describe
    overlapping real-world validity when their system-recording windows are
    disjoint, as with a retroactive correction whose predecessor is superseded
    exactly when the correction is recorded. A conflict exists only when two
    ``org_member_primary`` assertions for the same tenant-qualified canonical
    subject overlap in both real-world validity and system-recording history.
    Secondary and observed memberships are intentionally independent.

    Args:
        assertions: Assertion history to validate as one admission set.

    Raises:
        TypeError: If the input is not a sequence of ``ContextAssertion`` values.
        ValueError: If two primary assertions for one subject overlap in both
            temporal dimensions.
    """
    if isinstance(assertions, (str, bytes)) or not isinstance(assertions, Sequence):
        raise TypeError("assertions must be a sequence")

    primaries_by_subject: dict[str, list[ContextAssertion]] = {}
    for assertion in assertions:
        if type(assertion) is not ContextAssertion:
            raise TypeError("assertions must contain ContextAssertion values")
        if assertion.predicate != "org_member_primary":
            continue
        primaries_by_subject.setdefault(str(assertion.subject), []).append(assertion)

    for subject, primaries in primaries_by_subject.items():
        for first, second in combinations(primaries, 2):
            if _primary_intervals_conflict(first.interval, second.interval):
                raise ValueError(
                    f"subject {subject!r} has overlapping org_member_primary "
                    "assertions in both valid and recorded time"
                )
