"""Reject regular-file replacement of release-attestation verification output."""

from __future__ import annotations

import base64
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
_EXPECTED_SBOM: dict[str, Any] = {
    "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
    "@graph": [
        {"type": "CreationInfo", "specVersion": "3.0.1"},
        {
            "type": "software_Package",
            "name": "cwl-context-contracts",
            "software_packageVersion": "0.1",
        },
    ],
}
_MISMATCHED_SBOM: dict[str, Any] = {
    **_EXPECTED_SBOM,
    "@graph": [
        {"type": "CreationInfo", "specVersion": "3.0.1"},
        {
            "type": "software_Package",
            "name": "different-signed-package",
            "software_packageVersion": "0.1",
        },
    ],
}


def _verification_result(
    artifact_digest: str,
    predicate: dict[str, Any],
    predicate_type: str,
) -> list[dict[str, Any]]:
    """Build one verified gh result carrying the exact signed DSSE statement."""
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"digest": {"sha256": artifact_digest}}],
        "predicateType": predicate_type,
        "predicate": predicate,
    }
    payload = json.dumps(statement, separators=(",", ":")).encode("utf-8")
    return [
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


def test_verifier_rejects_regular_output_replacement_after_gh_writes(
    tmp_path: Path,
) -> None:
    """Compare the signed predicate bytes received from gh, not a reopened pathname."""
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    wheel = evidence_dir / "cwl_context_contracts-0.1-py3-none-any.whl"
    sdist = evidence_dir / "cwl_context_contracts-0.1.tar.gz"
    sbom_path = evidence_dir / "cwl-context-contracts.spdx.json"
    wheel.write_bytes(b"wheel")
    sdist.write_bytes(b"sdist")
    sbom_path.write_text(json.dumps(_EXPECTED_SBOM), encoding="utf-8")
    evidence_files = [wheel, sdist, sbom_path]
    checksum_lines = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
        for path in sorted(evidence_files)
    ]
    (evidence_dir / "SHA256SUMS").write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
    )
    package_report = verify_package_evidence_directory(evidence_dir)
    assert package_report.verified
    package_snapshot = json.dumps(
        package_report.to_mapping(),
        sort_keys=True,
        separators=(",", ":"),
    )

    verification_dir = tmp_path / "verification"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'if [[ " $* " == *" --predicate-type "* ]]; then\n'
        '  printf \'%s\\n\' "$GH_FAKE_MISMATCHED_RESULT"\n'
        '  output_path="$GH_FAKE_VERIFICATION_DIR/$(basename "$3").sbom.json"\n'
        '  rm -f "$output_path"\n'
        '  printf \'%s\\n\' "$GH_FAKE_ATTACKER_RESULT" > "$output_path"\n'
        "else\n"
        '  printf \'%s\\n\' "$GH_FAKE_PROVENANCE_RESULT"\n'
        "fi\n",
        encoding="utf-8",
    )
    gh_path.chmod(0o755)

    wheel_digest = hashlib.sha256(b"wheel").hexdigest()
    provenance_result = json.dumps(
        _verification_result(
            wheel_digest,
            {},
            "https://slsa.dev/provenance/v1",
        )
    )
    mismatched_result = json.dumps(
        _verification_result(
            wheel_digest,
            _MISMATCHED_SBOM,
            "https://spdx.dev/Document/v3",
        )
    )
    attacker_result = json.dumps(
        _verification_result(
            wheel_digest,
            _EXPECTED_SBOM,
            "https://spdx.dev/Document/v3",
        )
    )
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "GH_FAKE_PROVENANCE_RESULT": provenance_result,
            "GH_FAKE_MISMATCHED_RESULT": mismatched_result,
            "GH_FAKE_ATTACKER_RESULT": attacker_result,
            "GH_FAKE_VERIFICATION_DIR": str(verification_dir),
            "SOURCE_SHA": _SOURCE_SHA,
            "SOURCE_REF": "refs/heads/main",
            "EXPECTED_SOURCE_REF": "refs/heads/main",
            "REPOSITORY": "ContextualWisdomLab/context-graph-contracts",
            "SIGNER_WORKFLOW": (
                "ContextualWisdomLab/context-graph-contracts/"
                ".github/workflows/supply-chain.yml"
            ),
            "SPDX_PREDICATE": "https://spdx.dev/Document/v3",
            "EXPECTED_PACKAGE_SNAPSHOT": package_snapshot,
            "EVIDENCE_DIR": str(evidence_dir),
            "VERIFICATION_DIR": str(verification_dir),
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
    expected_message = "attested SPDX predicate does not match downloaded package SBOM"
    assert expected_message in result.stderr
