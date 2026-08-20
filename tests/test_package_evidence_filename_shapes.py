"""Release-evidence acceptance for malformed package filename shapes."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import cwl_context_contracts

_SBOM_NAME = "cwl-context-contracts.spdx.json"


def _sha256(payload: bytes) -> str:
    """Return the lowercase SHA-256 digest used by the package workflow."""
    return hashlib.sha256(payload).hexdigest()


def _write_evidence(
    directory: Path,
    *,
    wheel_name: str,
    sdist_name: str,
) -> None:
    """Write one three-artifact bundle whose package names are under test."""
    payloads = {
        wheel_name: b"wheel-bytes",
        sdist_name: b"sdist-bytes",
        _SBOM_NAME: b"{}",
    }
    for name, payload in payloads.items():
        (directory / name).write_bytes(payload)
    (directory / "SHA256SUMS").write_text(
        "".join(
            f"{_sha256(payload)}  {name}\n"
            for name, payload in payloads.items()
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("wheel_name", "sdist_name"),
    [
        (
            "cwl_context_contracts-0.1.0.whl",
            "cwl_context_contracts-0.1.0.tar.gz",
        ),
        (
            "cwl_context_contracts-0.1.0-py3-none-any.whl",
            "cwl_context_contracts-0.1.0-rc1.tar.gz",
        ),
    ],
)
def test_malformed_release_filename_shape_fails_closed_as_artifact_set(
    tmp_path: Path,
    wheel_name: str,
    sdist_name: str,
) -> None:
    """Wrong wheel or sdist shapes cannot establish one coherent release version."""
    _write_evidence(tmp_path, wheel_name=wheel_name, sdist_name=sdist_name)

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("artifact_set",)
    assert {artifact.name for artifact in report.artifacts} == {
        wheel_name,
        sdist_name,
        _SBOM_NAME,
    }
