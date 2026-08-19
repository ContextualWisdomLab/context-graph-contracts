"""Buyer acceptance for one full installed contract release-admission decision."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import cwl_context_contracts
from cwl_context_contracts import contract_release_admission as admission_module


def _approved_conformance_manifest() -> dict[str, object]:
    """Return an independently mutable semantic-profile approval snapshot."""
    return json.loads(
        json.dumps(cwl_context_contracts.build_packaged_conformance_manifest().to_mapping())
    )


def _approved_bundle_manifest() -> dict[str, object]:
    """Return an independently mutable complete-bundle approval snapshot."""
    return json.loads(
        json.dumps(
            cwl_context_contracts.build_packaged_contract_bundle_manifest().to_mapping()
        )
    )


def test_release_admission_requires_semantics_and_complete_bundle_bytes() -> None:
    """One buyer decision passes only when both approved evidence layers pass."""
    report = cwl_context_contracts.evaluate_packaged_contract_release_admission(
        _approved_conformance_manifest(),
        _approved_bundle_manifest(),
    )

    assert report.admitted is True
    assert report.conformance_admission.admitted is True
    assert report.bundle_verification.verified is True
    assert report.to_mapping()["admission_format"] == (
        "cwl-context-contract-release-admission/v1"
    )
    assert report.next_action == (
        "verify artifact provenance, protected-release evidence, and runtime "
        "authorization before enabling the integration"
    )


def test_complete_bundle_drift_blocks_release_admission_after_semantic_success() -> None:
    """Semantic success cannot hide drift in a non-profile published resource."""
    approved_bundle = _approved_bundle_manifest()
    approved_bundle["distribution_version"] = "999.0.0"

    report = cwl_context_contracts.evaluate_packaged_contract_release_admission(
        _approved_conformance_manifest(),
        approved_bundle,
    )

    assert report.admitted is False
    assert report.conformance_admission.admitted is True
    assert report.bundle_verification.verified is False
    assert report.next_action == (
        "install the approved contract package or approve this exact bundle manifest"
    )


def test_conformance_manifest_drift_blocks_release_admission_with_matching_bundle() -> None:
    """Complete bundle identity cannot replace approved semantic-profile identity."""
    approved_conformance = _approved_conformance_manifest()
    approved_conformance["distribution_version"] = "999.0.0"

    report = cwl_context_contracts.evaluate_packaged_contract_release_admission(
        approved_conformance,
        _approved_bundle_manifest(),
    )

    assert report.admitted is False
    assert report.conformance_admission.admitted is False
    assert report.bundle_verification.verified is True
    assert report.next_action == (
        "install the approved contract package or approve this exact manifest"
    )


def test_release_admission_cli_emits_one_machine_readable_decision(
    tmp_path,
    capsys,
) -> None:
    """Automation receives one deterministic JSON decision and exit zero."""
    conformance_path = tmp_path / "approved-conformance.json"
    bundle_path = tmp_path / "approved-bundle.json"
    conformance_path.write_text(
        json.dumps(_approved_conformance_manifest()),
        encoding="utf-8",
    )
    bundle_path.write_text(json.dumps(_approved_bundle_manifest()), encoding="utf-8")

    exit_code = admission_module.main([str(conformance_path), str(bundle_path)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["admitted"] is True
    assert payload["conformance_admission"]["admitted"] is True
    assert payload["bundle_verification"]["verified"] is True
    assert captured.err == ""


def test_release_admission_cli_returns_exit_one_for_bundle_drift(
    tmp_path,
    capsys,
) -> None:
    """Automation receives a non-zero decision when complete bundle bytes drift."""
    approved_bundle = _approved_bundle_manifest()
    approved_bundle["distribution_version"] = "999.0.0"
    conformance_path = tmp_path / "approved-conformance.json"
    bundle_path = tmp_path / "approved-bundle.json"
    conformance_path.write_text(
        json.dumps(_approved_conformance_manifest()),
        encoding="utf-8",
    )
    bundle_path.write_text(json.dumps(approved_bundle), encoding="utf-8")

    exit_code = admission_module.main([str(conformance_path), str(bundle_path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["admitted"] is False
    assert payload["bundle_verification"]["verified"] is False


def test_release_admission_cli_fails_closed_on_approved_input_error(
    tmp_path,
    capsys,
) -> None:
    """The composed boundary reuses the bounded strict approved-input parser."""
    missing_conformance = tmp_path / "missing.json"
    bundle_path = tmp_path / "approved-bundle.json"
    bundle_path.write_text(json.dumps(_approved_bundle_manifest()), encoding="utf-8")

    exit_code = admission_module.main([str(missing_conformance), str(bundle_path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload == {
        "admission_format": "cwl-context-contract-release-admission/v1",
        "admitted": False,
        "error": "approved_manifest_unreadable",
        "next_action": (
            "provide readable approved conformance and complete-bundle manifest "
            "JSON objects"
        ),
    }


def test_release_admission_cli_is_installed_by_project_metadata() -> None:
    """Buyers receive the full release-admission gate in the built distribution."""
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["scripts"]["cwl-context-release-admit"] == (
        "cwl_context_contracts.contract_release_admission:main"
    )
