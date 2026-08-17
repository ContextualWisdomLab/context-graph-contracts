"""Buyer-facing conformance manifest acceptance tests."""

from __future__ import annotations

import hashlib
import json
import tomllib
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

import pytest

import cwl_context_contracts.conformance_manifest as manifest_module
from cwl_context_contracts import (
    ConformanceEvidenceManifest,
    ConformanceProfileEvidence,
    available_conformance_profile_names,
    build_packaged_conformance_manifest,
    conformance_profile_sha256,
)


def test_profile_digest_binds_exact_packaged_resource_bytes() -> None:
    """Each digest identifies the exact semantic profile bytes shipped to buyers."""
    for profile_name in available_conformance_profile_names():
        expected = hashlib.sha256(
            files("cwl_context_contracts.conformance")
            .joinpath(profile_name)
            .read_bytes()
        ).hexdigest()

        assert conformance_profile_sha256(profile_name) == expected


def test_profile_digest_rejects_unknown_resource() -> None:
    """Callers cannot manufacture integrity evidence for an unpublished profile."""
    with pytest.raises(ValueError, match="unknown conformance profile"):
        conformance_profile_sha256("future-profile.v2.json")


def test_manifest_lists_every_packaged_profile_with_sha256() -> None:
    """One deterministic manifest binds every published semantic profile."""
    manifest = build_packaged_conformance_manifest()
    names = available_conformance_profile_names()
    distribution_version = version("cwl-context-contracts")

    assert manifest == ConformanceEvidenceManifest(
        distribution_name="cwl-context-contracts",
        distribution_version=distribution_version,
        profiles=tuple(
            ConformanceProfileEvidence(
                profile_name=name,
                sha256=conformance_profile_sha256(name),
            )
            for name in names
        ),
    )
    assert manifest.profile_count == len(names)
    assert manifest.to_mapping() == {
        "manifest_format": "cwl-context-conformance-manifest/v1",
        "distribution_name": "cwl-context-contracts",
        "distribution_version": distribution_version,
        "algorithm": "sha256",
        "profile_count": len(names),
        "profiles": [
            {
                "profile_name": name,
                "sha256": conformance_profile_sha256(name),
            }
            for name in names
        ],
    }


def test_manifest_version_is_bound_to_installed_distribution_metadata() -> None:
    """Captured evidence identifies the installed contract distribution version."""
    manifest = build_packaged_conformance_manifest()

    assert manifest.distribution_name == "cwl-context-contracts"
    assert manifest.distribution_version == version(manifest.distribution_name)
    assert manifest.distribution_version


def test_manifest_cli_is_installed_by_project_metadata() -> None:
    """The buyer command resolves to the tested manifest entry point."""
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["scripts"]["cwl-context-conformance-manifest"] == (
        "cwl_context_contracts.conformance_manifest:main"
    )


def test_manifest_cli_prints_deterministic_machine_readable_evidence(capsys) -> None:
    """Release tooling can capture profile integrity evidence without Python code."""
    exit_code = manifest_module.main()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload == build_packaged_conformance_manifest().to_mapping()
    assert captured.err == ""
