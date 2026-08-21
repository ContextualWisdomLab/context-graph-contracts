"""Exercise the protected-release attestation verifier as an executable boundary."""

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
_REPOSITORY = "ContextualWisdomLab/context-graph-contracts"
_SIGNER_WORKFLOW = (
    "ContextualWisdomLab/context-graph-contracts/.github/workflows/supply-chain.yml"
)
_ARTIFACT_BYTES = b"artifact"
_REPLACEMENT_ARTIFACT_BYTES = b"replacement-artifact"
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


def _verification_result(
    artifact_digest: str,
    predicate: dict[str, Any],
    predicate_type: str,
) -> list[dict[str, Any]]:
    """Build gh's verified result together with the exact signed DSSE statement."""
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"digest": {"sha256": artifact_digest}}],
        "predicateType": predicate_type,
        "predicate": predicate,
    }
    signed_payload = json.dumps(
        statement,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return [
        {
            "attestation": {
                "bundle": {
                    "dsseEnvelope": {
                        "payload": base64.b64encode(signed_payload).decode("ascii"),
                        "payloadType": "application/vnd.in-toto+json",
                    }
                }
            },
            "verificationResult": {"statement": statement},
        }
    ]


def _write_fake_gh(tmp_path: Path) -> tuple[Path, Path]:
    """Create a deterministic gh shim that records every invocation."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_path = tmp_path / "gh.log"
    gh_path = bin_dir / "gh"
    gh_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'printf \'%s\\n\' "$*" >> "$GH_FAKE_LOG"\n'
        'if [[ -n "${GH_FAKE_REPLACEMENT_SBOM:-}" ]]; then\n'
        '  printf \'%s\\n\' "$GH_FAKE_REPLACEMENT_SBOM" > "$GH_FAKE_SBOM_PATH"\n'
        "fi\n"
        "if [[ \" $* \" == *\" --predicate-type \"* ]]; then\n"
        "  printf '%s\\n' \"$GH_FAKE_SBOM_RESULT\"\n"
        '  if [[ "${GH_FAKE_REPLACE_VERIFICATION_OUTPUTS:-0}" == "1" ]]; then\n'
        '    output_path="$GH_FAKE_VERIFICATION_DIR/$(basename "$3").sbom.json"\n'
        '    rm -f "$output_path"\n'
        '    ln -s "$GH_FAKE_ATTACKER_VERIFICATION_RESULT" "$output_path"\n'
        "  fi\n"
        "else\n"
        "  printf '%s\\n' \"$GH_FAKE_PROVENANCE_RESULT\"\n"
        '  if [[ -n "${GH_FAKE_REPLACEMENT_ARTIFACT_PATH:-}" ]] '
        '&& [[ "$3" == "$GH_FAKE_REPLACEMENT_ARTIFACT_PATH" ]]; then\n'
        '    printf \'%s\' "$GH_FAKE_REPLACEMENT_ARTIFACT" > "$3"\n'
        "  fi\n"
        "fi\n",
        encoding="utf-8",
    )
    gh_path.chmod(0o755)
    return bin_dir, log_path


def _package_snapshot(evidence_dir: Path) -> str:
    """Return the canonical build-job snapshot for one valid evidence bundle."""
    report = verify_package_evidence_directory(evidence_dir)
    if not report.verified:
        return "{}"
    return json.dumps(
        report.to_mapping(),
        sort_keys=True,
        separators=(",", ":"),
    )


def _run_verifier(
    tmp_path: Path,
    artifact_names: tuple[str, ...],
    *,
    source_ref: str = "refs/heads/main",
    attested_sbom: dict[str, Any] | None = None,
    include_downloaded_sbom: bool = True,
    replacement_downloaded_sbom: dict[str, Any] | None = None,
    replace_verification_outputs: bool = False,
    replace_artifact_between_attestations: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run the verifier with isolated evidence and a fake GitHub CLI."""
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    for artifact_name in artifact_names:
        (evidence_dir / artifact_name).write_bytes(_ARTIFACT_BYTES)
    sbom_path = evidence_dir / "cwl-context-contracts.spdx.json"
    if include_downloaded_sbom:
        sbom_path.write_text(
            json.dumps(_EXPECTED_SBOM),
            encoding="utf-8",
        )
        evidence_files = [evidence_dir / name for name in artifact_names]
        evidence_files.append(sbom_path)
        checksum_lines = [
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
            for path in sorted(evidence_files)
        ]
        (evidence_dir / "SHA256SUMS").write_text(
            "\n".join(checksum_lines) + "\n",
            encoding="utf-8",
        )

    bin_dir, log_path = _write_fake_gh(tmp_path)
    verification_dir = tmp_path / "verification"
    signed_sbom = _EXPECTED_SBOM if attested_sbom is None else attested_sbom
    initial_digest = hashlib.sha256(_ARTIFACT_BYTES).hexdigest()
    replacement_digest = hashlib.sha256(_REPLACEMENT_ARTIFACT_BYTES).hexdigest()
    sbom_artifact_digest = (
        replacement_digest if replace_artifact_between_attestations else initial_digest
    )
    provenance_result = _verification_result(
        initial_digest,
        {},
        "https://slsa.dev/provenance/v1",
    )
    sbom_result = _verification_result(
        sbom_artifact_digest,
        signed_sbom,
        "https://spdx.dev/Document/v3",
    )
    attacker_result_path = tmp_path / "attacker-verification-result.json"
    if replace_verification_outputs:
        attacker_result_path.write_text(
            json.dumps(
                _verification_result(
                    initial_digest,
                    _EXPECTED_SBOM,
                    "https://spdx.dev/Document/v3",
                )
            ),
            encoding="utf-8",
        )
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "GH_FAKE_LOG": str(log_path),
            "GH_FAKE_PROVENANCE_RESULT": json.dumps(provenance_result),
            "GH_FAKE_SBOM_RESULT": json.dumps(sbom_result),
            "GH_FAKE_SBOM_PATH": str(sbom_path),
            "GH_FAKE_REPLACE_VERIFICATION_OUTPUTS": (
                "1" if replace_verification_outputs else "0"
            ),
            "GH_FAKE_VERIFICATION_DIR": str(verification_dir),
            "GH_FAKE_ATTACKER_VERIFICATION_RESULT": str(attacker_result_path),
            "SOURCE_SHA": _SOURCE_SHA,
            "SOURCE_REF": source_ref,
            "EXPECTED_SOURCE_REF": "refs/heads/main",
            "REPOSITORY": _REPOSITORY,
            "SIGNER_WORKFLOW": _SIGNER_WORKFLOW,
            "SPDX_PREDICATE": "https://spdx.dev/Document/v3",
            "EXPECTED_PACKAGE_SNAPSHOT": _package_snapshot(evidence_dir),
            "EVIDENCE_DIR": str(evidence_dir),
            "VERIFICATION_DIR": str(verification_dir),
        }
    )
    if replacement_downloaded_sbom is not None:
        env["GH_FAKE_REPLACEMENT_SBOM"] = json.dumps(replacement_downloaded_sbom)
    if replace_artifact_between_attestations:
        env["GH_FAKE_REPLACEMENT_ARTIFACT_PATH"] = str(
            evidence_dir / artifact_names[0]
        )
        env["GH_FAKE_REPLACEMENT_ARTIFACT"] = _REPLACEMENT_ARTIFACT_BYTES.decode()
    return subprocess.run(
        ["bash", str(_SCRIPT_PATH)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_verifier_requires_one_wheel_and_one_sdist(tmp_path: Path) -> None:
    """Reject a same-count artifact set with the wrong package shape."""
    result = _run_verifier(
        tmp_path,
        (
            "cwl_context_contracts-0.1-py3-none-any.whl",
            "cwl_context_contracts-0.1-py3-none-linux.whl",
        ),
    )

    assert result.returncode != 0
    assert "expected exactly one wheel and one source distribution" in result.stderr


def test_verifier_requires_downloaded_spdx_document(tmp_path: Path) -> None:
    """Fail closed when the signed predicate has no downloaded SBOM to bind."""
    result = _run_verifier(
        tmp_path,
        (
            "cwl_context_contracts-0.1-py3-none-any.whl",
            "cwl_context_contracts-0.1.tar.gz",
        ),
        include_downloaded_sbom=False,
    )

    assert result.returncode != 0
    assert "expected one regular downloaded SPDX evidence document" in result.stderr
    assert not (tmp_path / "gh.log").exists()


def test_verifier_executes_both_attestation_policies(tmp_path: Path) -> None:
    """Verify exact producer identity and both predicates for both release artifacts."""
    result = _run_verifier(
        tmp_path,
        (
            "cwl_context_contracts-0.1-py3-none-any.whl",
            "cwl_context_contracts-0.1.tar.gz",
        ),
    )

    assert result.returncode == 0, result.stderr
    log_lines = (tmp_path / "gh.log").read_text(encoding="utf-8").splitlines()
    assert len(log_lines) == 4
    assert (
        sum(
            "--predicate-type https://spdx.dev/Document/v3" in line
            for line in log_lines
        )
        == 2
    )
    assert all(f"--repo {_REPOSITORY}" in line for line in log_lines)
    assert all(f"--source-digest {_SOURCE_SHA}" in line for line in log_lines)
    assert all("--source-ref refs/heads/main" in line for line in log_lines)
    assert all(f"--signer-digest {_SOURCE_SHA}" in line for line in log_lines)
    assert all(f"--signer-workflow {_SIGNER_WORKFLOW}" in line for line in log_lines)
    assert all(
        "--cert-oidc-issuer https://token.actions.githubusercontent.com" in line
        for line in log_lines
    )
    assert all("--deny-self-hosted-runners" in line for line in log_lines)

    verification_files = sorted(
        path.name for path in (tmp_path / "verification").glob("*.json")
    )
    assert verification_files == [
        "cwl_context_contracts-0.1-py3-none-any.whl.provenance.json",
        "cwl_context_contracts-0.1-py3-none-any.whl.sbom.json",
        "cwl_context_contracts-0.1.tar.gz.provenance.json",
        "cwl_context_contracts-0.1.tar.gz.sbom.json",
    ]


def test_verifier_rejects_non_release_ref_before_calling_gh(tmp_path: Path) -> None:
    """Fail closed before any attestation lookup outside protected main."""
    result = _run_verifier(
        tmp_path,
        (
            "cwl_context_contracts-0.1-py3-none-any.whl",
            "cwl_context_contracts-0.1.tar.gz",
        ),
        source_ref="refs/heads/develop",
    )

    assert result.returncode != 0
    assert "refusing attestation verification outside protected main" in result.stderr
    assert not (tmp_path / "gh.log").exists()


def test_verifier_rejects_attested_spdx_predicate_drift(tmp_path: Path) -> None:
    """Reject an SPDX attestation whose signed predicate is not the downloaded SBOM."""
    attested_sbom = {
        **_EXPECTED_SBOM,
        "@graph": [
            {
                "type": "software_Package",
                "name": "different-package",
            }
        ],
    }
    result = _run_verifier(
        tmp_path,
        (
            "cwl_context_contracts-0.1-py3-none-any.whl",
            "cwl_context_contracts-0.1.tar.gz",
        ),
        attested_sbom=attested_sbom,
    )

    assert result.returncode != 0
    assert (
        "attested SPDX predicate does not match downloaded package SBOM"
        in result.stderr
    )


def test_verifier_rejects_mid_verification_downloaded_sbom_replacement(
    tmp_path: Path,
) -> None:
    """Bind the attestation to the SBOM snapshot present before GitHub verification."""
    replacement_sbom = {
        **_EXPECTED_SBOM,
        "@graph": [
            {
                "type": "software_Package",
                "name": "replacement-package",
            }
        ],
    }
    result = _run_verifier(
        tmp_path,
        (
            "cwl_context_contracts-0.1-py3-none-any.whl",
            "cwl_context_contracts-0.1.tar.gz",
        ),
        attested_sbom=replacement_sbom,
        replacement_downloaded_sbom=replacement_sbom,
    )

    assert result.returncode != 0
    assert (
        "attested SPDX predicate does not match downloaded package SBOM"
        in result.stderr
    )


def test_verifier_rejects_artifact_replacement_between_attestation_checks(
    tmp_path: Path,
) -> None:
    """Require provenance and SPDX statements to bind the same artifact bytes."""
    result = _run_verifier(
        tmp_path,
        (
            "cwl_context_contracts-0.1-py3-none-any.whl",
            "cwl_context_contracts-0.1.tar.gz",
        ),
        replace_artifact_between_attestations=True,
    )

    assert result.returncode != 0
    assert "attestation subject does not match release artifact" in result.stderr


def test_verifier_rejects_mid_verification_output_symlink_replacement(
    tmp_path: Path,
) -> None:
    """Reject verification output replaced after gh writes the signed predicate."""
    mismatched_sbom = {
        **_EXPECTED_SBOM,
        "@graph": [
            {
                "type": "software_Package",
                "name": "different-signed-package",
            }
        ],
    }
    result = _run_verifier(
        tmp_path,
        (
            "cwl_context_contracts-0.1-py3-none-any.whl",
            "cwl_context_contracts-0.1.tar.gz",
        ),
        attested_sbom=mismatched_sbom,
        replace_verification_outputs=True,
    )

    assert result.returncode != 0
