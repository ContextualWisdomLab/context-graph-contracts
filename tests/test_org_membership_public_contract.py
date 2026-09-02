"""Public conformance regressions for organization-membership semantics."""

from __future__ import annotations

from copy import deepcopy

import pytest

from cwl_context_contracts import (
    ContextAssertion,
    assert_ancestor_closure_chain,
    assert_single_primary_membership_per_subject,
    available_fixture_names,
    load_fixture,
)


def _fixture() -> dict[str, object]:
    """Return a fresh mapping from the installed organization fixture corpus."""
    return load_fixture("valid-org-membership.json")


def _assertion(value: dict[str, object]) -> ContextAssertion:
    """Parse one organization-membership assertion from a test mapping."""
    return ContextAssertion.from_mapping(value)


def test_org_membership_fixtures_are_public_package_inventory() -> None:
    """Installed consumers can load both advertised organization fixtures."""
    names = available_fixture_names()
    assert "valid-org-membership.json" in names
    assert "invalid-org-membership.json" in names
    assert load_fixture("invalid-org-membership.json")["predicate"] == "org_member_primary"


def test_public_ancestor_validator_rejects_skipped_hierarchy_level() -> None:
    """An ancestor closure cannot silently skip a hierarchy level."""
    value = _fixture()
    memberships = value["memberships"]
    assert isinstance(memberships, list)
    memberships[0]["membership_level"] = 5
    memberships[1]["membership_level"] = 3
    memberships[2]["membership_level"] = 2

    with pytest.raises(ValueError, match="exactly one"):
        assert_ancestor_closure_chain(_assertion(value))


def test_public_ancestor_validator_requires_zero_level_root() -> None:
    """A null-parent terminal node is a root only at membership level zero."""
    value = _fixture()
    memberships = value["memberships"]
    assert isinstance(memberships, list)
    memberships[0]["membership_level"] = 3
    memberships[1]["membership_level"] = 2
    memberships[2]["membership_level"] = 1

    with pytest.raises(ValueError, match="root.*0"):
        assert_ancestor_closure_chain(_assertion(value))


def test_primary_history_accepts_retroactive_correction_after_supersession() -> None:
    """Disjoint recording windows may describe overlapping real-world validity."""
    original = _fixture()
    original_interval = original["interval"]
    assert isinstance(original_interval, dict)
    original_interval["superseded_at"] = "2026-03-01T00:00:00Z"

    corrected = deepcopy(original)
    corrected["assertion_id"] = "0195d145-64e8-7f4f-8a23-a0cc784cb813"
    corrected_interval = corrected["interval"]
    assert isinstance(corrected_interval, dict)
    corrected_interval["recorded_at"] = "2026-03-01T00:00:00Z"
    corrected_interval["superseded_at"] = None

    assert_single_primary_membership_per_subject(
        [_assertion(original), _assertion(corrected)]
    )


def test_primary_history_rejects_simultaneously_known_validity_overlap() -> None:
    """Two primary facts may not overlap in both valid and recording dimensions."""
    first = _fixture()
    second = deepcopy(first)
    second["assertion_id"] = "0195d145-64e8-7f4f-8a23-a0cc784cb814"
    second_interval = second["interval"]
    assert isinstance(second_interval, dict)
    second_interval["recorded_at"] = "2026-02-01T00:00:00Z"

    with pytest.raises(ValueError, match="overlapping org_member_primary"):
        assert_single_primary_membership_per_subject(
            [_assertion(first), _assertion(second)]
        )
