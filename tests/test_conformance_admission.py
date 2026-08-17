"""Buyer acceptance for one-step semantic conformance admission evidence."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import cwl_context_contracts
from cwl_context_contracts import conformance_admission as admission_module


def _approved_manifest() -> dict[str, object]:
    """Return an independently mutable approved-manifest snapshot."""
    return json.loads(
        json.dumps(cwl_context_contracts.build_packaged_conformance_manifest().to_mapping())
    )


def test_exact_manifest_and_semantic_suite_are_both_required_for_admission() -> None:
    """A buyer receives one decision only when both deterministic gates pass."""
    report = cwl_context_contracts.evaluate_packaged_conformance_admission(
        _approved_manifest()
    )

    assert report.admitted is True
    assert report.conformance_report.passed is True
    assert report.manifest_verification.verified is True
    assert report.next_action == (
        "verify artifact provenance and runtime authorization before enabling "
        "the integration"
    )
    payload = report.to_mapping()
    assert payload["admission_format"] == "cwl-context-conformance-admission/v1"
    assert payload["admitted"] is True
    assert payload["semantic_conformance"]["status"] == "pass"
    assert payload["manifest_verification"]["verified"] is True


def test_manifest_drift_blocks_admission_after_semantic_success() -> None:
    """Passing semantics cannot authorize a package whose approved bytes drifted."""
    approved = _approved_manifest()
    approved["distribution_version"] = "999.0.0"

    report = cwl_context_contracts.evaluate_packaged_conformance_admission(approved)

    assert report.admitted is False
    assert report.conformance_report.passed is True
    assert report.manifest_verification.verified is False
    assert report.next_action == (
        "install the approved contract package or approve this exact manifest"
    )


def test_semantic_failure_blocks_admission_even_when_manifest_matches(
    monkeypatch,
) -> None:
    """Matching profile bytes cannot hide a broken installed reference SDK."""
    failed_report = cwl_context_contracts.ConformanceReport(
        profile_count=1,
        case_count=1,
        failures=(
            cwl_context_contracts.ConformanceFailure(
                profile_name="cwl-timestamp-profile.v1.json",
                case_id="valid_values[0]",
                detail="valid vector was unexpectedly rejected",
            ),
        ),
    )
    monkeypatch.setattr(
        admission_module,
        "run_packaged_conformance",
        lambda: failed_report,
    )

    report = cwl_context_contracts.evaluate_packaged_conformance_admission(
        _approved_manifest()
    )

    assert report.admitted is False
    assert report.conformance_report is failed_report
    assert report.manifest_verification.verified is True
    assert report.next_action == (
        "repair installed semantic conformance before enabling the integration"
    )


def test_admission_cli_accepts_exact_manifest_and_emits_machine_readable_evidence(
    tmp_path, capsys
) -> None:
    """Automation gets one stable JSON admission decision and exit zero."""
    approved_path = tmp_path / "approved.json"
    approved_path.write_text(json.dumps(_approved_manifest()), encoding="utf-8")

    exit_code = admission_module.main([str(approved_path)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["admitted"] is True
    assert payload["semantic_conformance"]["status"] == "pass"
    assert payload["manifest_verification"]["verified"] is True
    assert captured.err == ""


def test_admission_cli_returns_exit_one_for_evidence_drift(tmp_path, capsys) -> None:
    """Automation receives exit one when either deterministic admission gate fails."""
    approved = _approved_manifest()
    approved["distribution_version"] = "999.0.0"
    approved_path = tmp_path / "approved.json"
    approved_path.write_text(json.dumps(approved), encoding="utf-8")

    exit_code = admission_module.main([str(approved_path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["admitted"] is False
    assert payload["manifest_verification"]["verified"] is False


def test_admission_cli_reuses_fail_closed_manifest_input_boundary(
    tmp_path, capsys
) -> None:
    """The composite command must not reintroduce a permissive manifest parser."""
    missing_path = tmp_path / "missing.json"

    exit_code = admission_module.main([str(missing_path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload == {
        "admission_format": "cwl-context-conformance-admission/v1",
        "admitted": False,
        "error": "approved_manifest_unreadable",
        "next_action": "provide a readable approved conformance manifest JSON object",
    }


def test_admission_cli_is_installed_by_project_metadata() -> None:
    """Buyers receive the composite admission gate in the built distribution."""
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["scripts"]["cwl-context-conformance-admit"] == (
        "cwl_context_contracts.conformance_admission:main"
    )
