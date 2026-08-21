"""Protect release-attestation predicate identity from lossy JSON number parsing."""

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
_ARTIFACT_BYTES = b"artifact"


def _verification_result(
    statement_bytes: bytes,
    parsed_statement: dict[str, Any],
) -> list[dict[str, Any]]:
    """Pair an exact signed DSSE statement with gh's parsed statement view."""
    return [
        {
            "attestation": {
                "bundle": {
                    "dsseEnvelope": {
                        "payload": base64.b64encode(statement_bytes).decode("ascii"),
                        "payloadType": "application/vnd.in-toto+json",
                    }
                }
            },
            "verificationResult": {"statement": parsed_statement},
        }
    ]


def test_spdx_predicate_identity_rejects_distinct_large_decimal_values(
    tmp_path: Path,
) -> None:
    """Compare the signed DSSE payload, not gh's lossy parsed statement view."""
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    wheel = evidence_dir / "cwl_context_contracts-0.1-py3-none-any.whl"
    sdist = evidence_dir / "cwl_context_contracts-0.1.tar.gz"
    wheel.write_bytes(_ARTIFACT_BYTES)
    sdist.write_bytes(_ARTIFACT_BYTES)

    downloaded_sbom = (
        '{"@context":"https://spdx.org/rdf/3.0.1/spdx-context.jsonld",'
        '"@graph":[{"type":"CreationInfo","specVersion":"3.0.1"},'
        '{"type":"software_Package","name":"cwl-context-contracts",'
        '"software_packageVersion":"0.1",'
        '"precisionProbe":9007199254740992.0}]}'
    )
    signed_sbom = (
        '{"@context":"https://spdx.org/rdf/3.0.1/spdx-context.jsonld",'
        '"@graph":[{"type":"CreationInfo","specVersion":"3.0.1"},'
        '{"type":"software_Package","name":"cwl-context-contracts",'
        '"software_packageVersion":"0.1",'
        '"precisionProbe":9007199254740993.0}]}'
    )
    sbom_path = evidence_dir / "cwl-context-contracts.spdx.json"
    sbom_path.write_text(downloaded_sbom, encoding="utf-8")
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

    artifact_digest = hashlib.sha256(_ARTIFACT_BYTES).hexdigest()
    subject = [{"digest": {"sha256": artifact_digest}}]
    provenance_statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": subject,
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {},
    }
    provenance_bytes = json.dumps(
        provenance_statement,
        separators=(",", ":"),
    ).encode()
    provenance_result = _verification_result(
        provenance_bytes,
        provenance_statement,
    )

    signed_statement = (
        '{"_type":"https://in-toto.io/Statement/v1",'
        f'"subject":{json.dumps(subject, separators=(",", ":"))},'
        '"predicateType":"https://spdx.dev/Document/v3",'
        f'"predicate":{signed_sbom}'
        "}"
    ).encode()
    # sigstore-go materializes the verified statement as an in-toto protobuf.
    # Its generic predicate is a protobuf Struct, whose JSON number representation
    # is binary64. Simulate gh's parsed view rounding the signed 2^53+1 value down
    # to 2^53 while retaining the exact signed DSSE payload in the bundle.
    rounded_predicate = json.loads(downloaded_sbom)
    parsed_sbom_statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": subject,
        "predicateType": "https://spdx.dev/Document/v3",
        "predicate": rounded_predicate,
    }
    sbom_result = _verification_result(signed_statement, parsed_sbom_statement)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "if [[ \" $* \" == *\" --predicate-type \"* ]]; then\n"
        "  printf '%s\\n' \"$GH_FAKE_SBOM_RESULT\"\n"
        "else\n"
        "  printf '%s\\n' \"$GH_FAKE_PROVENANCE_RESULT\"\n"
        "fi\n",
        encoding="utf-8",
    )
    gh_path.chmod(0o755)

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "GH_FAKE_PROVENANCE_RESULT": json.dumps(provenance_result),
            "GH_FAKE_SBOM_RESULT": json.dumps(sbom_result),
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

    assert result.returncode != 0
    assert (
        "attested SPDX predicate does not match downloaded package SBOM"
        in result.stderr
    )
