"""Regression coverage for the SPDX 3 JSON-LD shape emitted by Syft."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cwl_context_contracts import verify_package_evidence_directory


def _sha256(payload: bytes) -> str:
    """Return the lowercase SHA-256 digest used by package evidence."""
    return hashlib.sha256(payload).hexdigest()


def test_syft_spdx_3_software_package_version_is_verified(tmp_path: Path) -> None:
    """Accept the profile-prefixed package version emitted by SPDX 3 JSON-LD."""
    wheel_name = "cwl_context_contracts-0.1.0-py3-none-any.whl"
    sdist_name = "cwl_context_contracts-0.1.0.tar.gz"
    sbom_name = "cwl-context-contracts.spdx.json"
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
        wheel_name: b"wheel",
        sdist_name: b"sdist",
        sbom_name: sbom,
    }
    for name, payload in artifacts.items():
        (tmp_path / name).write_bytes(payload)
    (tmp_path / "SHA256SUMS").write_text(
        "".join(
            f"{_sha256(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )

    report = verify_package_evidence_directory(tmp_path)

    assert report.verified is True
    assert report.mismatches == ()
