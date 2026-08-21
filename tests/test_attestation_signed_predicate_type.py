"""Bind retained attestation evidence to the expected signed predicate type."""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

_SCRIPT_PATH = Path("scripts/verify_attestation_output.py")
_PROVENANCE_PREDICATE = "https://slsa.dev/provenance/v1"
_SPDX_PREDICATE = "https://spdx.dev/Document/v3"
_ARTIFACT_BYTES = b"release-artifact"


def _verification_result(predicate_type: str) -> str:
    """Return gh-shaped JSON carrying one exact signed DSSE statement."""
    artifact_digest = hashlib.sha256(_ARTIFACT_BYTES).hexdigest()
    statement: dict[str, Any] = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"digest": {"sha256": artifact_digest}}],
        "predicateType": predicate_type,
        "predicate": {},
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
    return json.dumps(result)


def _run_verifier(
    tmp_path: Path,
    *,
    signed_predicate_type: str,
    expected_predicate_type: str,
) -> subprocess.CompletedProcess[str]:
    """Execute the verifier against one already-cryptographically-verified candidate."""
    output_path = tmp_path / "verification.json"
    artifact_digest = hashlib.sha256(_ARTIFACT_BYTES).hexdigest()
    return subprocess.run(
        [
            "python",
            str(_SCRIPT_PATH),
            str(output_path),
            artifact_digest,
            expected_predicate_type,
        ],
        input=_verification_result(signed_predicate_type),
        check=False,
        capture_output=True,
        text=True,
    )


def test_verifier_accepts_exact_signed_predicate_type(tmp_path: Path) -> None:
    """Accept when the signed DSSE statement carries the required predicate type."""
    result = _run_verifier(
        tmp_path,
        signed_predicate_type=_PROVENANCE_PREDICATE,
        expected_predicate_type=_PROVENANCE_PREDICATE,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "verification.json").is_file()


def test_verifier_rejects_wrong_signed_predicate_type(tmp_path: Path) -> None:
    """Do not rely only on gh's parsed/default predicate policy for retained evidence."""
    result = _run_verifier(
        tmp_path,
        signed_predicate_type=_SPDX_PREDICATE,
        expected_predicate_type=_PROVENANCE_PREDICATE,
    )

    assert result.returncode != 0
    assert "attestation predicate type does not match expected policy" in result.stderr
    assert not (tmp_path / "verification.json").exists()
