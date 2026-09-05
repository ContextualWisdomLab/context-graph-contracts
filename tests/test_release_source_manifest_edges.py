"""Hostile and packaging edge cases for release-source manifest generation."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

import cwl_context_contracts
from cwl_context_contracts import release_source_manifest as manifest_module

_REPOSITORY = "ContextualWisdomLab/context-graph-contracts"
_SOURCE_REF = "refs/heads/main"
_SOURCE_SHA = "fedcba9876543210fedcba9876543210fedcba98"
_SIGNER = f"{_REPOSITORY}/.github/workflows/supply-chain.yml"
_NEXT_ACTION = (
    "verify artifact attestations bind these exact package bytes to the intended "
    "protected main source commit before release"
)


def _snapshot() -> dict[str, object]:
    """Return one minimal valid verified package snapshot."""
    return {
        "verification_format": "cwl-context-package-evidence-verification/v1",
        "verified": True,
        "artifacts": [
            {
                "name": "cwl_context_contracts-0.1.0-py3-none-any.whl",
                "sha256": "a" * 64,
            },
            {
                "name": "cwl_context_contracts-0.1.0.tar.gz",
                "sha256": "b" * 64,
            },
            {
                "name": "cwl-context-contracts.spdx.json",
                "sha256": "c" * 64,
            },
        ],
        "mismatches": [],
        "next_action": _NEXT_ACTION,
    }


def _build(snapshot: dict[str, object]) -> manifest_module.ReleaseSourceManifest:
    """Build through the canonical source identity used by all edge tests."""
    return manifest_module.build_release_source_manifest(
        snapshot,
        source_repository=_REPOSITORY,
        source_ref=_SOURCE_REF,
        source_commit_sha=_SOURCE_SHA,
        signer_workflow=_SIGNER,
    )


def _cli(path: Path) -> int:
    """Invoke the manifest CLI with the one authorized source identity."""
    return manifest_module.main(
        [
            str(path),
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


@pytest.mark.parametrize(
    "mutator",
    [
        lambda value: value.__setitem__("unexpected", True),
        lambda value: value.__setitem__("verification_format", "wrong"),
        lambda value: value.__setitem__("next_action", "wrong"),
        lambda value: value.__setitem__("artifacts", "not-a-list"),
    ],
)
def test_snapshot_shape_and_verification_contract_fail_closed(mutator) -> None:
    """Only the exact verified package-snapshot shape can enter source binding."""
    snapshot = _snapshot()
    mutator(snapshot)

    with pytest.raises(manifest_module.ReleaseSourceManifestInputError):
        _build(snapshot)


@pytest.mark.parametrize(
    "artifacts",
    [
        [
            "not-an-object",
            {
                "name": "cwl_context_contracts-0.1.0.tar.gz",
                "sha256": "b" * 64,
            },
            {
                "name": "cwl-context-contracts.spdx.json",
                "sha256": "c" * 64,
            },
        ],
        [
            {"name": "cwl_context_contracts-0.1.0-py3-none-any.whl"},
            {
                "name": "cwl_context_contracts-0.1.0.tar.gz",
                "sha256": "b" * 64,
            },
            {
                "name": "cwl-context-contracts.spdx.json",
                "sha256": "c" * 64,
            },
        ],
        [
            {
                "name": "cwl_context_contracts-0.1.0-py3-none-any.whl",
                "sha256": "a" * 64,
            },
            {
                "name": "cwl_context_contracts-0.1.0.tar.gz",
                "sha256": "b" * 64,
            },
            {"name": "other.json", "sha256": "c" * 64},
        ],
        [
            {
                "name": "cwl_context_contracts-0.1.0.whl",
                "sha256": "a" * 64,
            },
            {
                "name": "cwl_context_contracts-0.1.0.tar.gz",
                "sha256": "b" * 64,
            },
            {
                "name": "cwl-context-contracts.spdx.json",
                "sha256": "c" * 64,
            },
        ],
    ],
)
def test_artifact_object_set_and_filename_contract_fail_closed(artifacts) -> None:
    """Reject malformed objects, missing SBOM identity, and malformed filenames."""
    snapshot = _snapshot()
    snapshot["artifacts"] = artifacts

    with pytest.raises(
        manifest_module.ReleaseSourceManifestInputError,
        match="package_snapshot_artifacts_invalid",
    ):
        _build(snapshot)


def test_malformed_json_snapshot_is_not_treated_as_evidence(
    tmp_path: Path,
    capsys,
) -> None:
    """JSON parse failure returns the stable invalid-input outcome."""
    path = tmp_path / "package-evidence-verification.json"
    path.write_text("{", encoding="utf-8")

    exit_code = _cli(path)

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["generated"] is False
    assert payload["error"] == "package_snapshot_invalid"
    assert payload["manifest_format"] == "cwl-context-release-source-manifest/v1"


def test_duplicate_json_member_is_rejected_before_schema_validation(
    tmp_path: Path,
    capsys,
) -> None:
    """Duplicate members fail even when the last value would remain schema-valid."""
    payload = json.dumps(_snapshot(), separators=(",", ":"))
    expected_member = (
        '"verification_format":"cwl-context-package-evidence-verification/v1"'
    )
    duplicate_member = f"{expected_member},{expected_member}"
    payload = payload.replace(expected_member, duplicate_member, 1)
    path = tmp_path / "duplicate-member.json"
    path.write_text(payload, encoding="utf-8")

    exit_code = _cli(path)
    result = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert result["error"] == "package_snapshot_invalid"


def test_nonstandard_json_constant_is_rejected_by_strict_loader(
    tmp_path: Path,
) -> None:
    """NaN is rejected by parsing before package-snapshot schema validation."""
    path = tmp_path / "nan.json"
    path.write_text('{"value":NaN}', encoding="utf-8")

    with pytest.raises(
        manifest_module.ReleaseSourceManifestInputError,
        match="package_snapshot_invalid",
    ):
        manifest_module._load_package_snapshot(path)


def test_deep_json_snapshot_returns_stable_cli_error(
    tmp_path: Path,
    capsys,
) -> None:
    """Excessive JSON nesting cannot escape the stable CLI error contract."""
    path = tmp_path / "deep.json"
    nesting = manifest_module._MAX_JSON_DEPTH + 1
    path.write_text("[" * nesting + "]" * nesting, encoding="utf-8")

    exit_code = _cli(path)
    result = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert result["generated"] is False
    assert result["error"] == "package_snapshot_too_deep"


def test_package_snapshot_input_is_bounded(tmp_path: Path, capsys) -> None:
    """Oversized release metadata fails before JSON parsing or hashing."""
    path = tmp_path / "oversized.json"
    path.write_bytes(b"{" + b" " * (1024 * 1024) + b"}")

    exit_code = _cli(path)
    result = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert result["error"] == "package_snapshot_too_large"


def test_release_source_manifest_is_public_sdk_and_installed_cli() -> None:
    """Generated SDK and operator CLI expose the same release-source contract."""
    assert cwl_context_contracts.ReleaseSourceManifest is (
        manifest_module.ReleaseSourceManifest
    )
    assert cwl_context_contracts.ReleaseSourceArtifact is (
        manifest_module.ReleaseSourceArtifact
    )
    assert cwl_context_contracts.ReleaseSourceManifestInputError is (
        manifest_module.ReleaseSourceManifestInputError
    )
    assert cwl_context_contracts.build_release_source_manifest is (
        manifest_module.build_release_source_manifest
    )

    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["scripts"]["cwl-context-release-source-manifest"] == (
        "cwl_context_contracts.release_source_manifest:main"
    )
