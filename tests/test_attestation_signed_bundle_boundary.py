"""Exercise the exact signed-DSSE boundary behind attestation admission."""

from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path
from typing import Any

_SCRIPT_PATH = Path("scripts/verify_attestation_output.py")
_ARTIFACT_DIGEST = "a" * 64


def _run_verifier(
    tmp_path: Path,
    verification: Any,
) -> subprocess.CompletedProcess[str]:
    """Run the stream verifier against one isolated gh-format JSON value."""
    return subprocess.run(
        [
            "python",
            str(_SCRIPT_PATH),
            str(tmp_path / "verified.json"),
            _ARTIFACT_DIGEST,
        ],
        input=json.dumps(verification),
        check=False,
        capture_output=True,
        text=True,
    )


def _candidate(
    *,
    payload: str,
    payload_type: str = "application/vnd.in-toto+json",
) -> dict[str, Any]:
    """Build one gh-format verified candidate around caller-controlled DSSE text."""
    return {
        "attestation": {
            "bundle": {
                "dsseEnvelope": {
                    "payload": payload,
                    "payloadType": payload_type,
                }
            }
        },
        "verificationResult": {"statement": {}},
    }


def _subject_statement() -> dict[str, Any]:
    """Return one exact signed statement matching the test artifact."""
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"digest": {"sha256": _ARTIFACT_DIGEST}}],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {},
    }


def _subject_statement_payload() -> str:
    """Return base64 for one exact signed statement matching the test artifact."""
    serialized = json.dumps(_subject_statement(), separators=(",", ":")).encode("utf-8")
    return base64.b64encode(serialized).decode("ascii")


def test_verifier_requires_signed_bundle_for_verified_candidate(tmp_path: Path) -> None:
    """A parsed verification result without its paired signed bundle is not evidence."""
    result = _run_verifier(tmp_path, [{"verificationResult": {"statement": {}}}])

    assert result.returncode != 0
    assert "verified attestation is missing its signed bundle" in result.stderr
    assert not (tmp_path / "verified.json").exists()


def test_verifier_requires_parsed_statement_marker_from_gh(tmp_path: Path) -> None:
    """A bundle is admissible only when gh also reports a parsed verified statement."""
    candidate = _candidate(payload=_subject_statement_payload())
    candidate["verificationResult"] = {}

    result = _run_verifier(tmp_path, [candidate])

    assert result.returncode != 0
    assert "verified attestation is missing its parsed statement" in result.stderr
    assert not (tmp_path / "verified.json").exists()


def test_verifier_requires_parsed_statement_to_match_signed_payload(
    tmp_path: Path,
) -> None:
    """Do not admit a signed payload different from the statement gh reports verified."""
    candidate = _candidate(payload=_subject_statement_payload())
    candidate["verificationResult"]["statement"] = {
        **_subject_statement(),
        "predicate": {"different": True},
    }

    result = _run_verifier(tmp_path, [candidate])

    assert result.returncode != 0
    assert "parsed verified statement does not match signed DSSE payload" in result.stderr
    assert not (tmp_path / "verified.json").exists()


def test_verifier_rejects_non_intoto_dsse_payload_type(tmp_path: Path) -> None:
    """Do not interpret arbitrary signed bytes as an in-toto statement."""
    payload = base64.b64encode(b"{}").decode("ascii")
    result = _run_verifier(
        tmp_path,
        [_candidate(payload=payload, payload_type="application/octet-stream")],
    )

    assert result.returncode != 0
    assert "unexpected DSSE payload type" in result.stderr
    assert not (tmp_path / "verified.json").exists()


def test_verifier_rejects_invalid_base64_signed_payload(tmp_path: Path) -> None:
    """Fail closed instead of accepting a malformed serialized DSSE payload."""
    result = _run_verifier(tmp_path, [_candidate(payload="***not-base64***")])

    assert result.returncode != 0
    assert "invalid base64 DSSE payload" in result.stderr
    assert not (tmp_path / "verified.json").exists()


def test_verifier_rejects_duplicate_members_in_signed_statement(tmp_path: Path) -> None:
    """The signed statement itself must satisfy the strict JSON identity grammar."""
    signed = (
        '{"subject":[{"digest":{"sha256":"'
        + _ARTIFACT_DIGEST
        + '"}}],"predicate":{},"predicate":{"different":true}}'
    ).encode("utf-8")
    result = _run_verifier(
        tmp_path,
        [_candidate(payload=base64.b64encode(signed).decode("ascii"))],
    )

    assert result.returncode != 0
    assert "duplicate JSON member: predicate" in result.stderr
    assert not (tmp_path / "verified.json").exists()


def test_verifier_rejects_non_object_signed_statement(tmp_path: Path) -> None:
    """A signed JSON scalar or array cannot masquerade as an in-toto statement."""
    payload = base64.b64encode(b"[]").decode("ascii")
    result = _run_verifier(tmp_path, [_candidate(payload=payload)])

    assert result.returncode != 0
    assert "signed DSSE payload must be an in-toto JSON object" in result.stderr
    assert not (tmp_path / "verified.json").exists()
