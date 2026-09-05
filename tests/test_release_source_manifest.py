"""Release-source manifest contract tests for immutable package provenance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from cwl_context_contracts import release_source_manifest as manifest_module

_REPOSITORY = "ContextualWisdomLab/context-graph-contracts"
_SOURCE_REF = "refs/heads/main"
_SOURCE_SHA = "0123456789abcdef0123456789abcdef01234567"
_SIGNER = f"{_REPOSITORY}/.github/workflows/supply-chain.yml"


def _artifact(name: str, digest_character: str) -> dict[str, str]:
    """Return one deterministic package-snapshot artifact record."""
    return {"name": name, "sha256": digest_character * 64}


def _package_snapshot(version: str = "0.1.0") -> dict[str, object]:
    """Return one verified exact package-evidence snapshot."""
    return {
        "verification_format": "cwl-context-package-evidence-verification/v1",
        "verified": True,
        "artifacts": [
            _artifact(f"cwl_context_contracts-{version}-py3-none-any.whl", "1"),
            _artifact(f"cwl_context_contracts-{version}.tar.gz", "2"),
            _artifact("cwl-context-contracts.spdx.json", "3"),
        ],
        "mismatches": [],
        "next_action": (
            "verify artifact attestations bind these exact package bytes to the "
            "intended protected main source commit before release"
        ),
    }


def _build(snapshot: dict[str, object] | None = None):
    """Build one manifest through the canonical protected-source boundary."""
    return manifest_module.build_release_source_manifest(
        _package_snapshot() if snapshot is None else snapshot,
        source_repository=_REPOSITORY,
        source_ref=_SOURCE_REF,
        source_commit_sha=_SOURCE_SHA,
        signer_workflow=_SIGNER,
    )


def test_manifest_binds_package_snapshot_and_protected_source_identity() -> None:
    """One manifest must bind exact package digests to one protected source SHA."""
    snapshot = _package_snapshot()

    manifest = _build(snapshot)
    payload = manifest.to_mapping()
    canonical_snapshot = json.dumps(
        snapshot,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    assert payload == {
        "manifest_format": "cwl-context-release-source-manifest/v1",
        "distribution_name": "cwl-context-contracts",
        "distribution_version": "0.1.0",
        "release_tag": "v0.1.0",
        "source_repository": _REPOSITORY,
        "source_ref": _SOURCE_REF,
        "source_commit_sha": _SOURCE_SHA,
        "signer_workflow": _SIGNER,
        "algorithm": "sha256",
        "package_snapshot_sha256": hashlib.sha256(canonical_snapshot).hexdigest(),
        "artifacts": snapshot["artifacts"],
        "next_action": (
            "independently verify this manifest's artifact attestation against the "
            "same repository, protected ref, source SHA, and signer workflow before "
            "treating its source fields as release provenance"
        ),
    }


def test_unverified_or_mismatched_package_snapshot_is_rejected() -> None:
    """A self-asserted or already-mismatched package snapshot cannot be promoted."""
    for snapshot in (
        {**_package_snapshot(), "verified": False},
        {**_package_snapshot(), "mismatches": ["artifact_sha256:wheel"]},
    ):
        with pytest.raises(
            manifest_module.ReleaseSourceManifestInputError,
            match="package_snapshot_not_verified",
        ):
            _build(snapshot)


def test_package_snapshot_requires_exact_unique_release_artifact_set() -> None:
    """Duplicate, malformed, or cross-version artifacts fail closed."""
    duplicate = _package_snapshot()
    duplicate["artifacts"] = [
        _artifact("cwl_context_contracts-0.1.0-py3-none-any.whl", "1"),
        _artifact("cwl_context_contracts-0.1.0-py3-none-any.whl", "2"),
        _artifact("cwl-context-contracts.spdx.json", "3"),
    ]
    cross_version = _package_snapshot()
    cross_version["artifacts"] = [
        _artifact("cwl_context_contracts-0.1.0-py3-none-any.whl", "1"),
        _artifact("cwl_context_contracts-0.2.0.tar.gz", "2"),
        _artifact("cwl-context-contracts.spdx.json", "3"),
    ]
    malformed_digest = _package_snapshot()
    malformed_digest["artifacts"] = [
        _artifact("cwl_context_contracts-0.1.0-py3-none-any.whl", "1"),
        _artifact("cwl_context_contracts-0.1.0.tar.gz", "2"),
        {"name": "cwl-context-contracts.spdx.json", "sha256": "not-a-digest"},
    ]

    for snapshot in (duplicate, cross_version, malformed_digest):
        with pytest.raises(
            manifest_module.ReleaseSourceManifestInputError,
            match="package_snapshot_artifacts_invalid",
        ):
            _build(snapshot)


def test_source_identity_is_exact_and_cannot_be_self_selected() -> None:
    """Source repository, ref, SHA, and signer identity are fixed contracts."""
    invalid_inputs = (
        {"source_repository": "ContextualWisdomLab/other"},
        {"source_ref": "refs/heads/develop"},
        {"source_commit_sha": "abc"},
        {"signer_workflow": "ContextualWisdomLab/other/.github/workflows/ci.yml"},
    )
    defaults = {
        "source_repository": _REPOSITORY,
        "source_ref": _SOURCE_REF,
        "source_commit_sha": _SOURCE_SHA,
        "signer_workflow": _SIGNER,
    }

    for override in invalid_inputs:
        with pytest.raises(manifest_module.ReleaseSourceManifestInputError):
            manifest_module.build_release_source_manifest(
                _package_snapshot(),
                **(defaults | override),
            )


def test_cli_emits_deterministic_manifest_for_verified_snapshot(
    tmp_path: Path,
    capsys,
) -> None:
    """Release automation receives deterministic JSON for later attestation."""
    snapshot_path = tmp_path / "package-evidence-verification.json"
    snapshot_path.write_text(json.dumps(_package_snapshot()), encoding="utf-8")

    exit_code = manifest_module.main(
        [
            str(snapshot_path),
            "--source-repository",
            _REPOSITORY,
            "--source-ref",
            _SOURCE_REF,
            "--source-sha",
            _SOURCE_SHA,
            "--signer-workflow",
            _SIGNER,
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["source_commit_sha"] == _SOURCE_SHA
    assert payload["distribution_version"] == "0.1.0"
    assert captured.err == ""


def test_cli_fails_closed_on_unreadable_or_invalid_snapshot(
    tmp_path: Path,
    capsys,
) -> None:
    """Release automation distinguishes unreadable input from rejected evidence."""
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("[]", encoding="utf-8")

    missing_exit = manifest_module.main(
        [
            str(tmp_path / "missing.json"),
            "--source-repository",
            _REPOSITORY,
            "--source-ref",
            _SOURCE_REF,
            "--source-sha",
            _SOURCE_SHA,
            "--signer-workflow",
            _SIGNER,
        ]
    )
    missing_payload = json.loads(capsys.readouterr().out)
    invalid_exit = manifest_module.main(
        [
            str(invalid_path),
            "--source-repository",
            _REPOSITORY,
            "--source-ref",
            _SOURCE_REF,
            "--source-sha",
            _SOURCE_SHA,
            "--signer-workflow",
            _SIGNER,
        ]
    )
    invalid_payload = json.loads(capsys.readouterr().out)

    assert missing_exit == 2
    assert missing_payload["error"] == "package_snapshot_unreadable"
    assert invalid_exit == 2
    assert invalid_payload["error"] == "package_snapshot_invalid"
