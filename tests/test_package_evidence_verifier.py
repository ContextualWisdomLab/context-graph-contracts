"""Buyer acceptance for exact package checksum and SPDX evidence verification."""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

import pytest

import cwl_context_contracts
from cwl_context_contracts import package_evidence_verifier as verifier_module


_WHEEL_NAME = "cwl_context_contracts-0.1.0-py3-none-any.whl"
_SDIST_NAME = "cwl_context_contracts-0.1.0.tar.gz"
_SBOM_NAME = "cwl-context-contracts.spdx.json"


def _sha256(payload: bytes) -> str:
    """Return the lowercase SHA-256 digest used by the package workflow."""
    return hashlib.sha256(payload).hexdigest()


def _valid_spdx() -> bytes:
    """Return the smallest SPDX 3.0.1 document accepted by the workflow contract."""
    return json.dumps(
        {
            "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
            "@graph": [
                {"type": "CreationInfo", "specVersion": "3.0.1"},
                {"type": "software_Package", "name": "cwl-context-contracts"},
            ],
        },
        sort_keys=True,
    ).encode()


def _write_valid_evidence(directory: Path) -> dict[str, bytes]:
    """Write one realistic supply-chain evidence bundle and return its payloads."""
    payloads = {
        _WHEEL_NAME: b"wheel-bytes",
        _SDIST_NAME: b"sdist-bytes",
        _SBOM_NAME: _valid_spdx(),
    }
    for name, payload in payloads.items():
        (directory / name).write_bytes(payload)
    (directory / "SHA256SUMS").write_text(
        "".join(f"{_sha256(payload)}  {name}\n" for name, payload in payloads.items()),
        encoding="utf-8",
    )
    return payloads


def test_exact_package_evidence_passes_with_machine_readable_artifact_identity(
    tmp_path: Path,
) -> None:
    """Exact wheel, sdist, SPDX and checksum evidence produces one positive decision."""
    payloads = _write_valid_evidence(tmp_path)

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is True
    assert report.mismatches == ()
    assert report.to_mapping()["verification_format"] == (
        "cwl-context-package-evidence-verification/v1"
    )
    assert report.to_mapping()["artifacts"] == [
        {"name": name, "sha256": _sha256(payloads[name])}
        for name in sorted(payloads)
    ]
    assert report.next_action == (
        "verify artifact attestations bind these exact package bytes to the intended "
        "protected main source commit before release"
    )


def test_tampered_artifact_fails_closed_without_relabeling_checksum_evidence(
    tmp_path: Path,
) -> None:
    """A post-build byte change is rejected even when SHA256SUMS remains unchanged."""
    _write_valid_evidence(tmp_path)
    (tmp_path / _WHEEL_NAME).write_bytes(b"tampered-wheel")

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == (f"artifact_sha256:{_WHEEL_NAME}",)
    assert report.next_action == (
        "rebuild or reacquire exact package evidence before provenance and release "
        "verification"
    )


def test_checksum_manifest_must_cover_exact_release_artifact_kinds(tmp_path: Path) -> None:
    """The evidence set cannot omit the wheel, sdist, or canonical SPDX document."""
    payloads = _write_valid_evidence(tmp_path)
    (tmp_path / "SHA256SUMS").write_text(
        f"{_sha256(payloads[_WHEEL_NAME])}  {_WHEEL_NAME}\n",
        encoding="utf-8",
    )

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("artifact_set",)


def test_checksum_manifest_rejects_path_traversal_and_duplicate_entries(
    tmp_path: Path,
) -> None:
    """Hostile checksum names and duplicate artifact identities fail at the input boundary."""
    _write_valid_evidence(tmp_path)
    digest = "0" * 64
    (tmp_path / "SHA256SUMS").write_text(
        f"{digest}  ../escape.whl\n{digest}  ../escape.whl\n",
        encoding="utf-8",
    )

    with pytest.raises(verifier_module.PackageEvidenceInputError) as exc_info:
        cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert exc_info.value.error_code == "checksum_manifest_invalid"


def test_symlinked_package_artifact_is_not_followed(tmp_path: Path) -> None:
    """Evidence verification refuses symlink substitution outside the evidence bundle."""
    payloads = _write_valid_evidence(tmp_path)
    outside = tmp_path.parent / "outside-wheel"
    outside.write_bytes(payloads[_WHEEL_NAME])
    (tmp_path / _WHEEL_NAME).unlink()
    (tmp_path / _WHEEL_NAME).symlink_to(outside)

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == (f"artifact_unsafe:{_WHEEL_NAME}",)


def test_spdx_document_must_preserve_3_0_1_package_evidence_shape(
    tmp_path: Path,
) -> None:
    """Checksum equality cannot hide a malformed or wrong-version SPDX document."""
    payloads = _write_valid_evidence(tmp_path)
    invalid_sbom = json.dumps(
        {"@context": "https://spdx.org/rdf/3.0/spdx-context.jsonld", "@graph": []}
    ).encode()
    (tmp_path / _SBOM_NAME).write_bytes(invalid_sbom)
    payloads[_SBOM_NAME] = invalid_sbom
    (tmp_path / "SHA256SUMS").write_text(
        "".join(f"{_sha256(payload)}  {name}\n" for name, payload in payloads.items()),
        encoding="utf-8",
    )

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("sbom_spdx_3_0_1",)


def test_package_evidence_cli_emits_deterministic_success(tmp_path: Path, capsys) -> None:
    """Operators receive one JSON decision and exit zero for exact package evidence."""
    _write_valid_evidence(tmp_path)

    exit_code = verifier_module.main([str(tmp_path)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["verified"] is True
    assert payload["mismatches"] == []
    assert captured.err == ""


def test_package_evidence_cli_fails_closed_on_missing_directory(
    tmp_path: Path,
    capsys,
) -> None:
    """Unreadable evidence input returns a distinct operator-fixable exit code."""
    missing = tmp_path / "missing"

    exit_code = verifier_module.main([str(missing)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload == {
        "verification_format": "cwl-context-package-evidence-verification/v1",
        "verified": False,
        "error": "evidence_directory_unreadable",
        "next_action": "provide a readable package-evidence directory",
    }


def test_package_evidence_cli_is_installed_by_project_metadata() -> None:
    """Release operators receive the verifier in the built distribution."""
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["scripts"]["cwl-context-package-evidence-verify"] == (
        "cwl_context_contracts.package_evidence_verifier:main"
    )
