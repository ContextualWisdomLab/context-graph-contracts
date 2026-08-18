"""Failure-path coverage for the packaged data-management conformance runner."""

from __future__ import annotations

import cwl_context_contracts.conformance_runner as runner


def test_runner_reports_valid_data_management_vector_rejected_by_sdk(monkeypatch) -> None:
    """A published positive assessment vector rejected by the SDK is drift."""

    original_load = runner.load_conformance_profile

    def load_profile(name: str):
        profile = original_load(name)
        if name == "data-management-assessment-semantics.v1.json":
            profile["valid_vectors"] = [
                {
                    "case_id": "forced_valid_rejection",
                    "value": {"assessment_result_uri": "urn:cwl:test"},
                }
            ]
            profile["invalid_vectors"] = []
        return profile

    def reject_assessment(_value):
        raise ValueError("forced valid drift")

    monkeypatch.setattr(runner, "load_conformance_profile", load_profile)
    monkeypatch.setattr(
        runner,
        "validate_data_management_assessment_semantics",
        reject_assessment,
    )

    report = runner.run_packaged_conformance()

    failure = next(
        item
        for item in report.failures
        if item.profile_name == "data-management-assessment-semantics.v1.json"
    )
    assert failure.case_id == "forced_valid_rejection"
    assert "unexpectedly rejected" in failure.detail


def test_runner_reports_invalid_data_management_vector_accepted_by_sdk(monkeypatch) -> None:
    """A published negative assessment vector accepted by the SDK is drift."""

    original_load = runner.load_conformance_profile

    def load_profile(name: str):
        profile = original_load(name)
        if name == "data-management-assessment-semantics.v1.json":
            profile["valid_vectors"] = []
            profile["invalid_vectors"] = [
                {
                    "case_id": "forced_invalid_acceptance",
                    "error_pattern": "must reject",
                    "value": {"assessment_result_uri": "urn:cwl:test"},
                }
            ]
        return profile

    monkeypatch.setattr(runner, "load_conformance_profile", load_profile)
    monkeypatch.setattr(
        runner,
        "validate_data_management_assessment_semantics",
        lambda _value: None,
    )

    report = runner.run_packaged_conformance()

    failure = next(
        item
        for item in report.failures
        if item.profile_name == "data-management-assessment-semantics.v1.json"
    )
    assert failure.case_id == "forced_invalid_acceptance"
    assert "unexpectedly accepted" in failure.detail
