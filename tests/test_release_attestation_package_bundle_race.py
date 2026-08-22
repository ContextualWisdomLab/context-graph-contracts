"""Reject package-evidence replacement between build verification and attestation."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from cwl_context_contracts.package_evidence_verifier import (
    verify_package_evidence_directory,
)

_SCRIPT_PATH = Path("scripts/verify_release_attestations.sh")
_SOURCE_SHA = "a" * 40
_SPDX_PREDICATE = "https://spdx.dev/Document/v3"
_VERSION = "0.1.0"
_WHEEL_NAME = f"cwl_context_contracts-{_VERSION}-py3-none-any.whl"
_SDIST_NAME = f"cwl_context_contracts-{_VERSION}.tar.gz"
_SBOM_NAME = "cwl-context-contracts.spdx.json"


def _sbom(*, comment: str) -> dict[str, Any]:
    """Build one valid SPDX 3.0.1 package document with caller-visible identity."""
    return {
        "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
        "@graph": [
            {"type": "CreationInfo", "specVersion": "3.0.1"},
            {
                "type": "software_Package",
                "name": "cwl-context-contracts",
                "software_packageVersion": _VERSION,
                "comment": comment,
            },
        ],
    }


def _write_bundle(
    directory: Path,
    *,
    wheel_bytes: bytes,
    sdist_bytes: bytes,
    sbom: dict[str, Any],
) -> None:
    """Write one internally coherent package-evidence bundle."""
    directory.mkdir(exist_ok=True)
    sbom_bytes = json.dumps(sbom, sort_keys=True).encode("utf-8")
    files = {
        _WHEEL_NAME: wheel_bytes,
        _SDIST_NAME: sdist_bytes,
        _SBOM_NAME: sbom_bytes,
    }
    for name, data in files.items():
        (directory / name).write_bytes(data)
    checksum_lines = [
        f"{hashlib.sha256(data).hexdigest()}  {name}"
        for name, data in sorted(files.items())
    ]
    (directory / "SHA256SUMS").write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
    )


def _fake_gh_source() -> str:
    """Return a fake gh that verifies the artifact and SPDX bytes it receives."""
    return r'''#!/usr/bin/env python3
import base64
import hashlib
import json
import os
import sys
from pathlib import Path

artifact = Path(sys.argv[3])
args = sys.argv[4:]
predicate_type = None
for index, value in enumerate(args):
    if value.startswith("--predicate-type="):
        predicate_type = value.split("=", 1)[1]
        break
    if value == "--predicate-type":
        predicate_type = args[index + 1]
        break
if predicate_type is None:
    raise SystemExit("missing predicate type")

artifact_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
if predicate_type == os.environ["SPDX_PREDICATE"]:
    predicate = json.loads(Path(os.environ["SIGNED_SBOM_PATH"]).read_text())
else:
    predicate = {}
statement = {
    "_type": "https://in-toto.io/Statement/v1",
    "subject": [{"digest": {"sha256": artifact_digest}}],
    "predicateType": predicate_type,
    "predicate": predicate,
}
payload = json.dumps(statement, separators=(",", ":")).encode("utf-8")
result = [
    {
        "attestation": {
            "bundle": {
                "dsseEnvelope": {
                    "payload": base64.b64encode(payload).decode("ascii"),
                    "payloadType": "application/vnd.in-toto+json",
                }
            }
        },
        "verificationResult": {"statement": statement},
    }
]
print(json.dumps(result))
'''


def test_verifier_rejects_coherent_bundle_replacement_after_build_snapshot(
    tmp_path: Path,
) -> None:
    """Attest only the exact bundle verified and exported by the build job."""
    evidence_dir = tmp_path / "evidence"
    original_sbom = _sbom(comment="original")
    replacement_sbom = _sbom(comment="replacement")
    _write_bundle(
        evidence_dir,
        wheel_bytes=b"original-wheel",
        sdist_bytes=b"original-sdist",
        sbom=original_sbom,
    )
    original_report = verify_package_evidence_directory(evidence_dir)
    assert original_report.verified
    expected_snapshot = json.dumps(
        original_report.to_mapping(),
        sort_keys=True,
        separators=(",", ":"),
    )

    # Model a coherent workspace replacement after the package-evidence job has
    # already published its exact snapshot but before the attestation job signs.
    _write_bundle(
        evidence_dir,
        wheel_bytes=b"replacement-wheel",
        sdist_bytes=b"replacement-sdist",
        sbom=replacement_sbom,
    )
    assert verify_package_evidence_directory(evidence_dir).verified

    signed_sbom_path = tmp_path / "signed-sbom.json"
    signed_sbom_path.write_text(json.dumps(replacement_sbom), encoding="utf-8")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(_fake_gh_source(), encoding="utf-8")
    gh_path.chmod(0o755)

    verification_dir = tmp_path / "verification"
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "SOURCE_SHA": _SOURCE_SHA,
            "SOURCE_REF": "refs/heads/main",
            "EXPECTED_SOURCE_REF": "refs/heads/main",
            "REPOSITORY": "ContextualWisdomLab/context-graph-contracts",
            "SIGNER_WORKFLOW": (
                "ContextualWisdomLab/context-graph-contracts/"
                ".github/workflows/supply-chain.yml"
            ),
            "SPDX_PREDICATE": _SPDX_PREDICATE,
            "EVIDENCE_DIR": str(evidence_dir),
            "VERIFICATION_DIR": str(verification_dir),
            "SIGNED_SBOM_PATH": str(signed_sbom_path),
            "EXPECTED_PACKAGE_SNAPSHOT": expected_snapshot,
        }
    )

    result = subprocess.run(
        ["bash", str(_SCRIPT_PATH)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    assert "package evidence changed since build verification" in result.stderr
    assert not verification_dir.exists()
