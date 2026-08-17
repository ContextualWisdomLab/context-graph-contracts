"""Buyer acceptance for deterministic conformance admission receipts."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

import cwl_context_contracts
from cwl_context_contracts import conformance_admission_receipt as receipt_module


def _approved_manifest() -> dict[str, object]:
    """Return a mutable copy of the exact installed conformance manifest."""
    return json.loads(
        json.dumps(cwl_context_contracts.build_packaged_conformance_manifest().to_mapping())
    )


def test_receipt_binds_admission_and_approved_manifest_semantics() -> None:
    """A receipt identifies both the decision and the approved manifest content."""
    approved = _approved_manifest()

    receipt = cwl_context_contracts.build_packaged_conformance_admission_receipt(
        approved
    )

    assert receipt.admitted is True
    assert len(receipt.approved_manifest_canonical_sha256) == 64
    assert len(receipt.admission_evidence_sha256) == 64
    payload = receipt.to_mapping()
    assert payload["receipt_format"] == (
        "cwl-context-conformance-admission-receipt/v1"
    )
    assert payload["admitted"] is True
    assert payload["installed_distribution_name"] == "cwl-context-contracts"
    assert payload["approved_manifest_canonical_sha256"] == (
        receipt.approved_manifest_canonical_sha256
    )
    assert payload["admission_evidence_sha256"] == receipt.admission_evidence_sha256
    assert payload["next_action"] == (
        "verify artifact provenance and runtime authorization before enabling "
        "the integration"
    )


def test_manifest_digest_is_stable_across_json_member_order() -> None:
    """Equivalent approved JSON objects produce the same semantic manifest digest."""
    approved = _approved_manifest()
    reordered = dict(reversed(list(approved.items())))

    original = cwl_context_contracts.build_packaged_conformance_admission_receipt(
        approved
    )
    alternate = cwl_context_contracts.build_packaged_conformance_admission_receipt(
        reordered
    )

    assert original.approved_manifest_canonical_sha256 == (
        alternate.approved_manifest_canonical_sha256
    )
    assert original.admission_evidence_sha256 == alternate.admission_evidence_sha256


def test_manifest_digest_has_published_canonical_vector() -> None:
    """Other SDKs can reproduce one exact canonical-manifest receipt digest."""
    approved = {
        "manifest_format": "cwl-context-conformance-manifest/v1",
        "distribution_name": "cwl-context-contracts",
        "distribution_version": "999.0.0",
        "algorithm": "sha256",
        "profile_count": 1,
        "profiles": [
            {
                "profile_name": "x.json",
                "sha256": "0" * 64,
            }
        ],
    }

    receipt = cwl_context_contracts.build_packaged_conformance_admission_receipt(
        approved
    )

    assert receipt.admitted is False
    assert receipt.approved_manifest_canonical_sha256 == (
        "d2f075ded4291aa6a015359cb016632afe9cb0efe7097e23c02835a7685f95fa"
    )


def test_receipt_rejects_unknown_manifest_members_as_ambiguous_identity() -> None:
    """Unspecified JSON members cannot acquire an undocumented digest meaning."""
    approved = _approved_manifest()
    approved["untrusted_extension"] = 1.5

    with pytest.raises(ValueError, match="approved_manifest_invalid_shape"):
        cwl_context_contracts.build_packaged_conformance_admission_receipt(approved)


def test_manifest_digest_changes_when_approved_evidence_changes() -> None:
    """A changed approved profile digest cannot reuse the prior receipt identity."""
    approved = _approved_manifest()
    original = cwl_context_contracts.build_packaged_conformance_admission_receipt(
        approved
    )
    changed = _approved_manifest()
    profiles = changed["profiles"]
    assert isinstance(profiles, list)
    first_profile = profiles[0]
    assert isinstance(first_profile, dict)
    first_profile["sha256"] = "0" * 64

    drifted = cwl_context_contracts.build_packaged_conformance_admission_receipt(
        changed
    )

    assert drifted.admitted is False
    assert drifted.approved_manifest_canonical_sha256 != (
        original.approved_manifest_canonical_sha256
    )
    assert drifted.admission_evidence_sha256 != original.admission_evidence_sha256


def test_receipt_cli_emits_machine_readable_evidence(tmp_path, capsys) -> None:
    """Operators can persist one deterministic receipt from the installed package."""
    approved_path = tmp_path / "approved.json"
    approved_path.write_text(json.dumps(_approved_manifest()), encoding="utf-8")

    exit_code = receipt_module.main([str(approved_path)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["admitted"] is True
    assert len(payload["approved_manifest_canonical_sha256"]) == 64
    assert len(payload["admission_evidence_sha256"]) == 64
    assert captured.err == ""


def test_receipt_cli_returns_exit_one_for_manifest_drift(tmp_path, capsys) -> None:
    """Automation receives exit one and a new receipt when approved evidence drifts."""
    approved = _approved_manifest()
    approved["distribution_version"] = "999.0.0"
    approved_path = tmp_path / "approved.json"
    approved_path.write_text(json.dumps(approved), encoding="utf-8")

    exit_code = receipt_module.main([str(approved_path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["admitted"] is False
    assert len(payload["approved_manifest_canonical_sha256"]) == 64
    assert payload["next_action"] == (
        "install the approved contract package or approve this exact manifest"
    )


def test_receipt_cli_reuses_fail_closed_manifest_input_boundary(
    tmp_path, capsys
) -> None:
    """Receipt generation must not introduce a second permissive manifest parser."""
    missing_path = tmp_path / "missing.json"

    exit_code = receipt_module.main([str(missing_path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload == {
        "receipt_format": "cwl-context-conformance-admission-receipt/v1",
        "admitted": False,
        "error": "approved_manifest_unreadable",
        "next_action": "provide a readable approved conformance manifest JSON object",
    }


def test_receipt_cli_rejects_ambiguous_manifest_shape(tmp_path, capsys) -> None:
    """The CLI fails closed before hashing unspecified approved-manifest members."""
    approved = _approved_manifest()
    approved["untrusted_extension"] = 1.5
    approved_path = tmp_path / "approved.json"
    approved_path.write_text(json.dumps(approved), encoding="utf-8")

    exit_code = receipt_module.main([str(approved_path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["admitted"] is False
    assert payload["error"] == "approved_manifest_invalid_shape"


def test_receipt_cli_is_installed_by_project_metadata() -> None:
    """Built distributions expose the buyer-facing admission receipt command."""
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["scripts"]["cwl-context-conformance-receipt"] == (
        "cwl_context_contracts.conformance_admission_receipt:main"
    )
