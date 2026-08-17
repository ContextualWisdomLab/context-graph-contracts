"""Buyer-facing packaged conformance runner acceptance tests."""

from __future__ import annotations

import json

import pytest

import cwl_context_contracts.conformance_runner as runner
from cwl_context_contracts import (
    ConformanceFailure,
    ConformanceReport,
    assert_packaged_conformance,
    run_packaged_conformance,
)


def test_packaged_conformance_runner_executes_every_published_vector() -> None:
    """A buyer can execute every packaged semantic vector through one API call."""
    report = run_packaged_conformance()

    assert report.passed is True
    assert report.profile_count == 4
    assert report.case_count == 31
    assert report.failures == ()
    assert report.to_mapping() == {
        "status": "pass",
        "profile_count": 4,
        "case_count": 31,
        "failures": [],
    }


def test_assert_packaged_conformance_returns_successful_report() -> None:
    """The fail-closed assertion helper returns the verified report on success."""
    report = assert_packaged_conformance()

    assert report.passed is True


def test_runner_reports_a_valid_vector_that_reference_sdk_rejects(monkeypatch) -> None:
    """Conformance drift is surfaced with the exact profile and case identity."""
    original_load = runner.load_conformance_profile

    def load_profile(name: str):
        profile = original_load(name)
        if name == "cwl-timestamp-profile.v1.json":
            profile["valid_values"] = ["2026-02-30T12:00:00Z"]
            profile["invalid_values"] = []
        return profile

    monkeypatch.setattr(runner, "load_conformance_profile", load_profile)

    report = run_packaged_conformance()

    assert report.passed is False
    assert report.failures[0].profile_name == "cwl-timestamp-profile.v1.json"
    assert report.failures[0].case_id == "valid_values[0]"
    assert "unexpectedly rejected" in report.failures[0].detail


def test_runner_reports_invalid_vector_that_reference_sdk_accepts(monkeypatch) -> None:
    """A negative vector that becomes accepted is a deterministic failure."""
    original_load = runner.load_conformance_profile

    def load_profile(name: str):
        profile = original_load(name)
        if name == "context-assertion-semantics.v1.json":
            profile["invalid_vectors"] = []
        elif name == "cwl-json-interoperability.v1.json":
            profile["valid_integer_values"] = []
            profile["invalid_integer_values"] = [1]
        return profile

    monkeypatch.setattr(runner, "load_conformance_profile", load_profile)

    report = run_packaged_conformance()

    failure = next(
        item
        for item in report.failures
        if item.profile_name == "cwl-json-interoperability.v1.json"
    )
    assert failure.case_id == "invalid_integer_values[0]"
    assert "unexpectedly accepted" in failure.detail


def test_runner_reports_unexpected_error_text_for_negative_vector(monkeypatch) -> None:
    """Rejecting for the wrong reason does not satisfy a semantic vector."""
    original_load = runner.load_conformance_profile

    def load_profile(name: str):
        profile = original_load(name)
        if name == "cloudevent-semantics.v1.json":
            profile["valid_vectors"] = []
            profile["invalid_vectors"] = [
                {
                    "name": "wrong_reason",
                    "error_pattern": "different expected reason",
                    "value": {
                        "specversion": "0.3",
                    },
                }
            ]
        return profile

    monkeypatch.setattr(runner, "load_conformance_profile", load_profile)

    report = run_packaged_conformance()

    failure = next(
        item
        for item in report.failures
        if item.profile_name == "cloudevent-semantics.v1.json"
    )
    assert failure.case_id == "wrong_reason"
    assert "unexpected error" in failure.detail


def test_runner_reports_valid_cloudevent_that_cannot_round_trip(monkeypatch) -> None:
    """Canonicalization drift is not allowed to masquerade as vector success."""
    original_load = runner.load_conformance_profile

    def load_profile(name: str):
        profile = original_load(name)
        if name == "cloudevent-semantics.v1.json":
            vector = dict(profile["valid_vectors"][0])
            value = dict(vector["value"])
            value["time"] = "2026-08-16t00:00:00z"
            vector["name"] = "noncanonical_timestamp_spelling"
            vector["value"] = value
            profile["valid_vectors"] = [vector]
            profile["invalid_vectors"] = []
        return profile

    monkeypatch.setattr(runner, "load_conformance_profile", load_profile)

    report = run_packaged_conformance()

    failure = next(
        item
        for item in report.failures
        if item.profile_name == "cloudevent-semantics.v1.json"
    )
    assert failure.case_id == "noncanonical_timestamp_spelling"
    assert "round-trip exactly" in failure.detail


def test_runner_fails_closed_when_a_packaged_profile_cannot_load(monkeypatch) -> None:
    """A damaged installation becomes an explicit profile-load failure."""
    original_load = runner.load_conformance_profile

    def load_profile(name: str):
        if name == "cwl-timestamp-profile.v1.json":
            raise OSError("resource unreadable")
        return original_load(name)

    monkeypatch.setattr(runner, "load_conformance_profile", load_profile)

    report = run_packaged_conformance()

    assert report.passed is False
    assert report.failures[0] == ConformanceFailure(
        profile_name="cwl-timestamp-profile.v1.json",
        case_id="profile_load",
        detail="OSError: resource unreadable",
    )


def test_runner_fails_closed_for_an_unknown_packaged_profile(monkeypatch) -> None:
    """New profiles cannot silently bypass the executable conformance runner."""
    monkeypatch.setattr(
        runner,
        "available_conformance_profile_names",
        lambda: ("future-profile.v2.json",),
    )
    monkeypatch.setattr(
        runner,
        "load_conformance_profile",
        lambda _name: {"profile_id": "urn:cwl:future"},
    )

    report = run_packaged_conformance()

    assert report.profile_count == 1
    assert report.case_count == 0
    assert report.failures == (
        ConformanceFailure(
            profile_name="future-profile.v2.json",
            case_id="profile_dispatch",
            detail="no executable runner is registered for this packaged profile",
        ),
    )


def test_runner_fails_closed_when_profile_shape_is_not_executable(monkeypatch) -> None:
    """Malformed packaged data becomes a typed profile-execution failure."""
    original_load = runner.load_conformance_profile

    def load_profile(name: str):
        if name == "cwl-timestamp-profile.v1.json":
            return {"profile_id": "urn:cwl:broken"}
        return original_load(name)

    monkeypatch.setattr(runner, "load_conformance_profile", load_profile)

    report = run_packaged_conformance()

    assert report.failures[0].profile_name == "cwl-timestamp-profile.v1.json"
    assert report.failures[0].case_id == "profile_execution"
    assert report.failures[0].detail.startswith("KeyError:")


def test_assert_packaged_conformance_raises_with_actionable_failure(
    monkeypatch,
) -> None:
    """Gate callers fail closed with a concise first-failure identity."""
    report = ConformanceReport(
        profile_count=1,
        case_count=1,
        failures=(
            ConformanceFailure("profile.json", "case-1", "contract drift"),
        ),
    )
    monkeypatch.setattr(runner, "run_packaged_conformance", lambda: report)

    with pytest.raises(
        runner.ConformanceError,
        match=r"profile\.json/case-1: contract drift",
    ):
        runner.assert_packaged_conformance()


def test_cli_prints_machine_readable_pass_report(capsys) -> None:
    """Operators receive deterministic JSON suitable for release evidence."""
    exit_code = runner.main()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "pass"
    assert payload["case_count"] == 31
    assert captured.err == ""


def test_cli_returns_nonzero_for_conformance_drift(monkeypatch, capsys) -> None:
    """Automation receives a non-zero exit when semantic conformance fails."""
    report = ConformanceReport(
        profile_count=1,
        case_count=1,
        failures=(ConformanceFailure("profile.json", "case-1", "drift"),),
    )
    monkeypatch.setattr(runner, "run_packaged_conformance", lambda: report)

    exit_code = runner.main()

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload == {
        "case_count": 1,
        "failures": [
            {
                "case_id": "case-1",
                "detail": "drift",
                "profile_name": "profile.json",
            }
        ],
        "profile_count": 1,
        "status": "fail",
    }
