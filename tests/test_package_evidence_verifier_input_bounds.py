"""Fail-closed resource and JSON ambiguity tests for package evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import cwl_context_contracts
from cwl_context_contracts import package_evidence_verifier as verifier_module
from cwl_context_contracts.package_evidence_verifier import PackageEvidenceInputError


_SBOM_NAME = "cwl-context-contracts.spdx.json"


def _digest(payload: bytes) -> str:
    """Return the SHA-256 spelling used by the workflow checksum manifest."""
    return hashlib.sha256(payload).hexdigest()


def _valid_spdx() -> bytes:
    """Return the minimal package/version identity accepted by the verifier."""
    return b"""{
      "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
      "@graph": [
        {"type": "CreationInfo", "specVersion": "3.0.1"},
        {
          "type": "software_Package",
          "name": "cwl-context-contracts",
          "packageVersion": "0.1.0"
        }
      ]
    }"""


def _write_bundle(tmp_path: Path, sbom_payload: bytes) -> None:
    """Write one checksum-coherent package evidence bundle for release 0.1.0."""
    artifacts = {
        "cwl_context_contracts-0.1.0-py3-none-any.whl": b"wheel",
        "cwl_context_contracts-0.1.0.tar.gz": b"sdist",
        _SBOM_NAME: sbom_payload,
    }
    for name, payload in artifacts.items():
        (tmp_path / name).write_bytes(payload)
    (tmp_path / "SHA256SUMS").write_text(
        "".join(
            f"{_digest(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )


def test_duplicate_spdx_members_fail_closed(tmp_path: Path) -> None:
    """Ambiguous duplicate JSON members cannot authenticate package identity."""
    sbom_payload = b"""{
      "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
      "@graph": [
        {"type": "CreationInfo", "specVersion": "3.0.1"},
        {
          "type": "software_Package",
          "name": "cwl-context-contracts",
          "packageVersion": "9.9.9",
          "packageVersion": "0.1.0"
        }
      ]
    }"""
    _write_bundle(tmp_path, sbom_payload)

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("sbom_spdx_3_0_1",)


def test_nonstandard_spdx_numeric_constants_fail_closed(tmp_path: Path) -> None:
    """Python-only NaN syntax cannot enter portable SPDX release evidence."""
    sbom_payload = b"""{
      "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
      "@graph": [
        {"type": "CreationInfo", "specVersion": "3.0.1", "extra": NaN},
        {
          "type": "software_Package",
          "name": "cwl-context-contracts",
          "packageVersion": "0.1.0"
        }
      ]
    }"""
    _write_bundle(tmp_path, sbom_payload)

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("sbom_spdx_3_0_1",)


def test_checksum_manifest_read_is_bounded(tmp_path: Path) -> None:
    """An attacker-controlled checksum manifest cannot trigger an unbounded read."""
    oversized_manifest = b"0" * (verifier_module._MAX_CHECKSUM_MANIFEST_BYTES + 1)
    (tmp_path / "SHA256SUMS").write_bytes(oversized_manifest)

    with pytest.raises(PackageEvidenceInputError) as exc_info:
        cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert exc_info.value.error_code == "checksum_manifest_too_large"


def test_checksum_manifest_invalid_utf8_fails_closed(tmp_path: Path) -> None:
    """Checksum evidence must be a portable UTF-8 manifest."""
    (tmp_path / "SHA256SUMS").write_bytes(b"\xff")

    with pytest.raises(PackageEvidenceInputError) as exc_info:
        cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert exc_info.value.error_code == "checksum_manifest_unreadable"


def test_spdx_metadata_read_is_bounded(tmp_path: Path) -> None:
    """Oversized SBOM metadata fails closed without loading arbitrary bytes."""
    oversized_sbom = b" " * (verifier_module._MAX_SBOM_BYTES + 1)
    _write_bundle(tmp_path, oversized_sbom)

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("sbom_spdx_3_0_1",)


def test_spdx_invalid_utf8_fails_closed(tmp_path: Path) -> None:
    """SPDX package identity is not inferred from malformed text encoding."""
    _write_bundle(tmp_path, b"\xff")

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("sbom_spdx_3_0_1",)


def test_spdx_disappearing_after_digest_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A post-digest metadata disappearance remains a structured rejection."""
    _write_bundle(tmp_path, _valid_spdx())
    original_sha256_file = verifier_module._sha256_file

    def hash_then_remove(path: Path) -> str:
        digest = original_sha256_file(path)
        if path.name == _SBOM_NAME:
            path.unlink()
        return digest

    monkeypatch.setattr(verifier_module, "_sha256_file", hash_then_remove)

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("sbom_spdx_3_0_1",)
