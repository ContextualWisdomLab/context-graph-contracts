"""Bind retained attestation evidence to the expected signed statement policy."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

_SCRIPT_PATH = Path("scripts/verify_attestation_output.py")
_STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
_OTHER_STATEMENT_TYPE = "https://in-toto.io/Statement/v2"
_PROVENANCE_PREDICATE = "https://slsa.dev/provenance/v1"
_SPDX_PREDICATE = "https://spdx.dev/Document/v3"
_SOURCE_SHA = "a" * 40
_REPOSITORY = "ContextualWisdomLab/context-graph-contracts"
_SOURCE_REF = "refs/heads/main"
_WORKFLOW_PATH = ".github/workflows/supply-chain.yml"
_SIGNER_WORKFLOW = f"{_REPOSITORY}/{_WORKFLOW_PATH}"
_ARTIFACT_BYTES = b"release-artifact"


def _provenance_predicate() -> dict[str, Any]:
    """Return the policy-relevant SLSA predicate emitted by pinned actions/attest."""
    return {
        "buildDefinition": {
            "buildType": "https://actions.github.io/buildtypes/workflow/v1",
            "externalParameters": {
                "workflow": {
                    "ref": _SOURCE_REF,
                    "repository": f"https://github.com/{_REPOSITORY}",
                    "path": _WORKFLOW_PATH,
                }
            },
            "resolvedDependencies": [
                {
                    "uri": f"git+https://github.com/{_REPOSITORY}@{_SOURCE_REF}",
                    "digest": {"gitCommit": _SOURCE_SHA},
                }
            ],
        },
        "runDetails": {
            "builder": {
                "id": f"https://github.com/{_SIGNER_WORKFLOW}@{_SOURCE_REF}"
            }
        },
    }


def _verification_result(
    predicate_type: str,
    *,
    statement_type: str = _STATEMENT_TYPE,
) -> str:
    """Return gh-shaped JSON carrying one exact signed DSSE statement."""
    artifact_digest = hashlib.sha256(_ARTIFACT_BYTES).hexdigest()
    predicate = _provenance_predicate() if predicate_type == _PROVENANCE_PREDICATE else {}
    statement: dict[str, Any] = {
        "_type": statement_type,
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
    return json.dumps(result)


def _run_verifier(
    tmp_path: Path,
    *,
    signed_predicate_type: str,
    expected_predicate_type: str,
    statement_type: str = _STATEMENT_TYPE,
) -> subprocess.CompletedProcess[str]:
    """Execute the verifier against one already-cryptographically-verified candidate."""
    output_path = tmp_path / "verification.json"
    artifact_digest = hashlib.sha256(_ARTIFACT_BYTES).hexdigest()
    env = os.environ.copy()
    env.update(
        {
            "SOURCE_SHA": _SOURCE_SHA,
            "EXPECTED_SOURCE_REF": _SOURCE_REF,
            "REPOSITORY": _REPOSITORY,
            "SIGNER_WORKFLOW": _SIGNER_WORKFLOW,
        }
    )
    return subprocess.run(
        [
            "python",
            str(_SCRIPT_PATH),
            str(output_path),
            artifact_digest,
            expected_predicate_type,
        ],
        input=_verification_result(
            signed_predicate_type,
            statement_type=statement_type,
        ),
        check=False,
        capture_output=True,
        text=True,
        env=env,
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
    """Reject a signed predicate that differs from the retained evidence policy."""
    result = _run_verifier(
        tmp_path,
        signed_predicate_type=_SPDX_PREDICATE,
        expected_predicate_type=_PROVENANCE_PREDICATE,
    )

    assert result.returncode != 0
    assert "attestation predicate type does not match expected policy" in result.stderr
    assert not (tmp_path / "verification.json").exists()


def test_verifier_rejects_wrong_signed_statement_type(tmp_path: Path) -> None:
    """Require the authenticated payload to be an in-toto Statement v1 object."""
    result = _run_verifier(
        tmp_path,
        signed_predicate_type=_PROVENANCE_PREDICATE,
        expected_predicate_type=_PROVENANCE_PREDICATE,
        statement_type=_OTHER_STATEMENT_TYPE,
    )

    assert result.returncode != 0
    assert "signed DSSE statement type does not match in-toto v1" in result.stderr
    assert not (tmp_path / "verification.json").exists()
