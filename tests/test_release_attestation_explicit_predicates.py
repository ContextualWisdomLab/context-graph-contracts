"""Require explicit predicate selection for every release attestation lookup."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
from pathlib import Path

from cwl_context_contracts.package_evidence_verifier import (
    verify_package_evidence_directory,
)

_SCRIPT_PATH = Path("scripts/verify_release_attestations.sh")
_SOURCE_SHA = "a" * 40
_ARTIFACT_BYTES = b"artifact"
_ARTIFACT_DIGEST = hashlib.sha256(_ARTIFACT_BYTES).hexdigest()
_PROVENANCE_PREDICATE = "https://slsa.dev/provenance/v1"
_SPDX_PREDICATE = "https://spdx.dev/Document/v3"
_SBOM = {
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


def _signed_result(predicate_type: str, predicate: object) -> str:
    """Build one verified GitHub-style result with an exact signed statement."""
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"digest": {"sha256": _ARTIFACT_DIGEST}}],
        "predicateType": predicate_type,
        "predicate": predicate,
    }
    payload = base64.b64encode(
        json.dumps(statement, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    return json.dumps(
        [
            {
                "verificationResult": {"statement": statement},
                "attestation": {
                    "bundle": {
                        "dsseEnvelope": {
                            "payloadType": "application/vnd.in-toto+json",
                            "payload": payload,
                        }
                    }
                },
            }
        ]
    )


def test_every_attestation_lookup_selects_its_predicate_explicitly(
    tmp_path: Path,
) -> None:
    """Do not rely on the GitHub CLI default predicate when multiple types exist."""
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    wheel = evidence_dir / "cwl_context_contracts-0.1-py3-none-any.whl"
    sdist = evidence_dir / "cwl_context_contracts-0.1.tar.gz"
    sbom_path = evidence_dir / "cwl-context-contracts.spdx.json"
    wheel.write_bytes(_ARTIFACT_BYTES)
    sdist.write_bytes(_ARTIFACT_BYTES)
    sbom_path.write_text(json.dumps(_SBOM), encoding="utf-8")
    evidence_files = [wheel, sdist, sbom_path]
    checksum_lines = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
        for path in sorted(evidence_files)
    ]
    (evidence_dir / "SHA256SUMS").write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
    )
    report = verify_package_evidence_directory(evidence_dir)
    assert report.verified
    package_snapshot = json.dumps(
        report.to_mapping(),
        sort_keys=True,
        separators=(",", ":"),
    )

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'case " $* " in\n'
        f'  *" --predicate-type={_PROVENANCE_PREDICATE} "*) '
        'printf \'%s\\n\' "$GH_PROVENANCE" ;;\n'
        f'  *" --predicate-type {_SPDX_PREDICATE} "*) '
        'printf \'%s\\n\' "$GH_SBOM" ;;\n'
        '  *) echo "missing explicit predicate type" >&2; exit 9 ;;\n'
        "esac\n",
        encoding="utf-8",
    )
    gh_path.chmod(0o755)

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "GH_PROVENANCE": _signed_result(_PROVENANCE_PREDICATE, {}),
            "GH_SBOM": _signed_result(_SPDX_PREDICATE, _SBOM),
            "SOURCE_SHA": _SOURCE_SHA,
            "SOURCE_REF": "refs/heads/main",
            "EXPECTED_SOURCE_REF": "refs/heads/main",
            "REPOSITORY": "ContextualWisdomLab/context-graph-contracts",
            "SIGNER_WORKFLOW": (
                "ContextualWisdomLab/context-graph-contracts/"
                ".github/workflows/supply-chain.yml"
            ),
            "SPDX_PREDICATE": _SPDX_PREDICATE,
            "EXPECTED_PACKAGE_SNAPSHOT": package_snapshot,
            "EVIDENCE_DIR": str(evidence_dir),
            "VERIFICATION_DIR": str(tmp_path / "verification"),
        }
    )

    result = subprocess.run(
        ["bash", str(_SCRIPT_PATH)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
