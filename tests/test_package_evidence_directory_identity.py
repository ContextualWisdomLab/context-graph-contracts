"""Security acceptance for the package-evidence directory identity boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import cwl_context_contracts
from cwl_context_contracts.package_evidence_verifier import PackageEvidenceInputError


def _digest(payload: bytes) -> str:
    """Return the SHA-256 digest format emitted by the supply-chain workflow."""
    return hashlib.sha256(payload).hexdigest()


def _write_valid_evidence_bundle(evidence_directory: Path) -> None:
    """Write one internally coherent package-evidence bundle for release 0.1.0."""
    evidence_directory.mkdir()
    sbom = json.dumps(
        {
            "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
            "@graph": [
                {"type": "CreationInfo", "specVersion": "3.0.1"},
                {
                    "type": "software_Package",
                    "name": "cwl-context-contracts",
                    "software_packageVersion": "0.1.0",
                },
            ],
        },
        sort_keys=True,
    ).encode()
    artifacts = {
        "cwl_context_contracts-0.1.0-py3-none-any.whl": b"wheel",
        "cwl_context_contracts-0.1.0.tar.gz": b"sdist",
        "cwl-context-contracts.spdx.json": sbom,
    }
    for name, payload in artifacts.items():
        (evidence_directory / name).write_bytes(payload)
    (evidence_directory / "SHA256SUMS").write_text(
        "".join(
            f"{_digest(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )


def test_symlinked_evidence_directory_fails_closed(tmp_path: Path) -> None:
    """A caller cannot redirect the evidence-root identity through a directory symlink."""
    real_evidence = tmp_path / "real-evidence"
    _write_valid_evidence_bundle(real_evidence)
    supplied_evidence = tmp_path / "supplied-evidence"
    supplied_evidence.symlink_to(real_evidence, target_is_directory=True)

    with pytest.raises(PackageEvidenceInputError) as exc_info:
        cwl_context_contracts.verify_package_evidence_directory(supplied_evidence)

    assert exc_info.value.error_code == "evidence_directory_unsafe"
