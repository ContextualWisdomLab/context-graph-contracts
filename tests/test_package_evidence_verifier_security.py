"""Security regressions for package-evidence input ownership."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import cwl_context_contracts
from cwl_context_contracts.package_evidence_verifier import PackageEvidenceInputError


def _digest(payload: bytes) -> str:
    """Return one workflow-compatible SHA-256 digest."""
    return hashlib.sha256(payload).hexdigest()


def test_symlinked_checksum_manifest_is_not_followed(tmp_path: Path) -> None:
    """A checksum authority outside the supplied evidence directory fails closed."""
    artifacts = {
        "cwl_context_contracts-0.1.0-py3-none-any.whl": b"wheel",
        "cwl_context_contracts-0.1.0.tar.gz": b"sdist",
        "cwl-context-contracts.spdx.json": json.dumps(
            {
                "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
                "@graph": [
                    {"type": "CreationInfo", "specVersion": "3.0.1"},
                    {"type": "software_Package"},
                ],
            }
        ).encode(),
    }
    for name, payload in artifacts.items():
        (tmp_path / name).write_bytes(payload)

    outside = tmp_path.parent / f"{tmp_path.name}-outside-sha256sums"
    outside.write_text(
        "".join(
            f"{_digest(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )
    (tmp_path / "SHA256SUMS").symlink_to(outside)

    with pytest.raises(PackageEvidenceInputError) as exc_info:
        cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert exc_info.value.error_code == "checksum_manifest_unsafe"


def test_spdx_package_identity_must_match_context_contract_distribution(
    tmp_path: Path,
) -> None:
    """Checksummed SPDX evidence for a different package cannot verify this release."""
    artifacts = {
        "cwl_context_contracts-0.1.0-py3-none-any.whl": b"wheel",
        "cwl_context_contracts-0.1.0.tar.gz": b"sdist",
        "cwl-context-contracts.spdx.json": json.dumps(
            {
                "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
                "@graph": [
                    {"type": "CreationInfo", "specVersion": "3.0.1"},
                    {"type": "software_Package", "name": "unrelated-package"},
                ],
            },
            sort_keys=True,
        ).encode(),
    }
    for name, payload in artifacts.items():
        (tmp_path / name).write_bytes(payload)
    (tmp_path / "SHA256SUMS").write_text(
        "".join(
            f"{_digest(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("sbom_spdx_3_0_1",)
