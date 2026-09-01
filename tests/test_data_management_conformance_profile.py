"""Portable conformance evidence for data-management assessment semantics."""

from __future__ import annotations

from cwl_context_contracts import (
    available_conformance_profile_names,
    load_conformance_profile,
    run_packaged_conformance,
)

_PROFILE_NAME = "data-management-assessment-semantics.v1.json"


def test_data_management_semantics_are_packaged_as_executable_vectors() -> None:
    """Non-Python consumers receive portable authority and tenant regressions."""
    assert _PROFILE_NAME in available_conformance_profile_names()

    profile = load_conformance_profile(_PROFILE_NAME)
    case_ids = {str(vector["case_id"]) for vector in profile["invalid_vectors"]}
    assert {
        "cross_authority_supersession",
        "cross_tenant_subject",
        "duplicate_dimension_code",
        "future_knowledge_cutoff",
    } <= case_ids

    report = run_packaged_conformance()
    assert report.passed is True
    assert report.profile_count == 6
