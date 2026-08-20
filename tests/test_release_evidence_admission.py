"""Buyer acceptance for one complete release-evidence admission decision."""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

import cwl_context_contracts
from cwl_context_contracts import release_evidence_admission as admission_module

_SPDX_CONTEXT = "https://spdx.org/rdf/3.0.1/spdx-context.jsonld"


def _approved_conformance_manifest() -> dict[str, object]:
    """Return one independently mutable semantic-profile approval snapshot."""
    return json.loads(
        json.dumps(
            cwl_context_contracts.build_packaged_conformance_manifest().to_mapping()
        )
    )


def _approved_bundle_manifest() -> dict[str, object]:
    """Return one independently mutable complete-bundle approval snapshot."""
    return json.loads(
        json.dumps(
            cwl_context_contracts.build_packaged_contract_bundle_manifest().to_mapping()
        )
    )


def _write_package_evidence(directory: Path, version: str = "0.1.0") -> None:
    """Write one coherent package-evidence bundle for the selected release version."""
    wheel_name = f"cwl_context_contracts-{version}-py3-none-any.whl"
    sdist_name = f"cwl_context_contracts-{version}.tar.gz"
    sbom_name = "cwl-context-contracts.spdx.json"
    payloads = {
        wheel_name: b"wheel-bytes",
        sdist_name: b"sdist-bytes",
        sbom_name: json.dumps(
            {
                "@context": _SPDX_CONTEXT,
                "@graph": [
                    {"type": "CreationInfo", "specVersion": "3.0.1"},
                    {
                        "type": "software_Package",
                        "name": "cwl-context-contracts",
                        "software_packageVersion": version,
                    },
                ],
            },
            sort_keys=True,
        ).encode(),
    }
    for name, payload in payloads.items():
        (directory / name).write_bytes(payload)
    checksum_lines = [
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in payloads.items()
    ]
    (directory / "SHA256SUMS").write_text(
        "".join(checksum_lines),
        encoding="utf-8",
    )


def _write_approved_inputs(directory: Path) -> tuple[Path, Path]:
    """Write the two independently approved installed-contract manifests."""
    conformance_path = directory / "approved-conformance.json"
    bundle_path = directory / "approved-bundle.json"
    conformance_path.write_text(
        json.dumps(_approved_conformance_manifest()),
        encoding="utf-8",
    )
    bundle_path.write_text(
        json.dumps(_approved_bundle_manifest()),
        encoding="utf-8",
    )
    return conformance_path, bundle_path


def test_complete_release_evidence_admits_only_one_matching_distribution(
    tmp_path: Path,
) -> None:
    """Installed contract evidence and package bytes must identify one exact version."""
    _write_package_evidence(tmp_path)

    report = cwl_context_contracts.evaluate_release_evidence_admission(
        tmp_path,
        _approved_conformance_manifest(),
        _approved_bundle_manifest(),
    )

    assert report.admitted is True
    assert report.contract_release_admission.admitted is True
    assert report.package_evidence_verification.verified is True
    assert report.package_distribution_version == "0.1.0"
    assert report.release_mismatches == ()
    assert report.to_mapping()["admission_format"] == (
        "cwl-context-complete-release-evidence-admission/v1"
    )
    assert report.next_action == (
        "verify artifact attestations bind these exact package bytes to the intended "
        "protected main source commit, then satisfy independent review and release "
        "authorization before publication"
    )


def test_package_version_drift_blocks_otherwise_positive_release_evidence(
    tmp_path: Path,
) -> None:
    """A coherent package from another version cannot be spliced into admission."""
    _write_package_evidence(tmp_path, version="0.1.1")

    report = cwl_context_contracts.evaluate_release_evidence_admission(
        tmp_path,
        _approved_conformance_manifest(),
        _approved_bundle_manifest(),
    )

    assert report.contract_release_admission.admitted is True
    assert report.package_evidence_verification.verified is True
    assert report.package_distribution_version == "0.1.1"
    assert report.admitted is False
    assert report.release_mismatches == ("package_distribution_version",)
    assert report.next_action == (
        "rebuild or reacquire package evidence for installed distribution version "
        "0.1.0 before provenance verification"
    )


def test_package_digest_failure_blocks_complete_release_evidence(
    tmp_path: Path,
) -> None:
    """Installed semantic success cannot hide tampered release artifact bytes."""
    _write_package_evidence(tmp_path)
    wheel_path = tmp_path / "cwl_context_contracts-0.1.0-py3-none-any.whl"
    wheel_path.write_bytes(b"tampered-wheel")

    report = cwl_context_contracts.evaluate_release_evidence_admission(
        tmp_path,
        _approved_conformance_manifest(),
        _approved_bundle_manifest(),
    )

    assert report.admitted is False
    assert report.contract_release_admission.admitted is True
    assert report.package_evidence_verification.verified is False
    assert report.release_mismatches == ()
    assert report.next_action == (
        "rebuild or reacquire exact package evidence before provenance and release "
        "verification"
    )


def test_contract_admission_failure_precedes_package_provenance_action(
    tmp_path: Path,
) -> None:
    """Approved-contract drift remains fail-closed even with coherent package bytes."""
    _write_package_evidence(tmp_path)
    approved_bundle = _approved_bundle_manifest()
    approved_bundle["distribution_version"] = "999.0.0"

    report = cwl_context_contracts.evaluate_release_evidence_admission(
        tmp_path,
        _approved_conformance_manifest(),
        approved_bundle,
    )

    assert report.admitted is False
    assert report.contract_release_admission.admitted is False
    assert report.package_evidence_verification.verified is True
    assert report.next_action == (
        "install the approved contract package or approve this exact bundle manifest"
    )


def test_complete_release_evidence_cli_emits_machine_readable_success(
    tmp_path: Path,
    capsys,
) -> None:
    """Release automation receives one deterministic successful composition."""
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir()
    _write_package_evidence(evidence_directory)
    conformance_path, bundle_path = _write_approved_inputs(tmp_path)

    exit_code = admission_module.main(
        [str(evidence_directory), str(conformance_path), str(bundle_path)]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["admitted"] is True
    assert payload["package_distribution_version"] == "0.1.0"
    assert payload["release_mismatches"] == []
    assert captured.err == ""


def test_complete_release_evidence_cli_returns_one_for_version_drift(
    tmp_path: Path,
    capsys,
) -> None:
    """A coherent package for another version produces a rejected decision."""
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir()
    _write_package_evidence(evidence_directory, version="0.1.1")
    conformance_path, bundle_path = _write_approved_inputs(tmp_path)

    exit_code = admission_module.main(
        [str(evidence_directory), str(conformance_path), str(bundle_path)]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["admitted"] is False
    assert payload["release_mismatches"] == ["package_distribution_version"]


def test_complete_release_evidence_cli_fails_closed_on_approved_input_error(
    tmp_path: Path,
    capsys,
) -> None:
    """Unreadable independent approval input has a stable operator error."""
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir()
    _write_package_evidence(evidence_directory)
    missing_conformance = tmp_path / "missing-approved.json"
    bundle_path = tmp_path / "approved-bundle.json"
    bundle_path.write_text(json.dumps(_approved_bundle_manifest()), encoding="utf-8")

    exit_code = admission_module.main(
        [str(evidence_directory), str(missing_conformance), str(bundle_path)]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload == {
        "admission_format": "cwl-context-complete-release-evidence-admission/v1",
        "admitted": False,
        "error": "approved_manifest_unreadable",
        "next_action": (
            "provide readable package evidence and approved conformance and "
            "complete-bundle manifest inputs"
        ),
    }


def test_complete_release_evidence_cli_fails_closed_on_package_input_error(
    tmp_path: Path,
    capsys,
) -> None:
    """Malformed package evidence is distinguished from a rejected valid decision."""
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir()
    (evidence_directory / "SHA256SUMS").write_text("bad\n", encoding="utf-8")
    conformance_path, bundle_path = _write_approved_inputs(tmp_path)

    exit_code = admission_module.main(
        [str(evidence_directory), str(conformance_path), str(bundle_path)]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["admitted"] is False
    assert payload["error"] == "checksum_manifest_invalid"
    assert payload["next_action"] == (
        "provide readable package evidence and approved conformance and "
        "complete-bundle manifest inputs"
    )


def test_complete_release_evidence_cli_is_installed_by_project_metadata() -> None:
    """Release operators receive the composed fail-closed evidence gate."""
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["scripts"]["cwl-context-release-evidence-admit"] == (
        "cwl_context_contracts.release_evidence_admission:main"
    )
