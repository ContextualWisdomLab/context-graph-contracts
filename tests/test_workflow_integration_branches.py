"""Verify repository-owned workflows preserve truthful integration evidence."""

from __future__ import annotations

import re
from pathlib import Path

from cwl_context_contracts import available_conformance_profile_names

_CI_PATH = Path(".github/workflows/ci.yml")
_SUPPLY_CHAIN_PATH = Path(".github/workflows/supply-chain.yml")
_RECEIPT_PACKAGE_SMOKE_PATH = Path(".github/workflows/receipt-package-smoke.yml")
_REPRODUCIBILITY_PATH = Path(".github/workflows/reproducibility.yml")
_WORKFLOW_PATHS = (
    _CI_PATH,
    _SUPPLY_CHAIN_PATH,
    _RECEIPT_PACKAGE_SMOKE_PATH,
    _REPRODUCIBILITY_PATH,
)
_PUSH_BRANCHES_PATTERN = re.compile(
    r"(?m)^  push:\n    branches: \[([^\]]+)\]$"
)
_EXACT_SOURCE_SHA = "${{ github.event.pull_request.head.sha || github.sha }}"
_REQUIRED_EXACT_SOURCE_CHECKOUTS = {
    _CI_PATH: 2,
    _SUPPLY_CHAIN_PATH: 2,
    _RECEIPT_PACKAGE_SMOKE_PATH: 1,
    _REPRODUCIBILITY_PATH: 2,
}


def _push_branches(workflow_path: Path) -> set[str]:
    """Return the explicit push branches declared by one repository workflow."""
    workflow_text = workflow_path.read_text(encoding="utf-8")
    match = _PUSH_BRANCHES_PATTERN.search(workflow_text)
    assert match is not None, f"{workflow_path} must declare explicit push branches"
    return {
        branch.strip()
        for branch in match.group(1).split(",")
        if branch.strip()
    }


def test_repository_workflows_run_on_git_flow_integration_branches() -> None:
    """Require post-integration evidence on both develop and stable main pushes."""
    expected_branches = {"develop", "main"}
    for workflow_path in _WORKFLOW_PATHS:
        assert _push_branches(workflow_path) == expected_branches


def test_pr_capable_workflows_checkout_exact_source_head() -> None:
    """Bind PR evidence to the immutable source head rather than a merge ref."""
    exact_ref = f"ref: {_EXACT_SOURCE_SHA}"
    exact_expected_sha = f"EXPECTED_SHA: {_EXACT_SOURCE_SHA}"

    for workflow_path, required_count in _REQUIRED_EXACT_SOURCE_CHECKOUTS.items():
        workflow_text = workflow_path.read_text(encoding="utf-8")
        assert workflow_text.count(exact_ref) >= required_count, workflow_path
        assert exact_expected_sha in workflow_text, workflow_path


def test_dependency_lock_name_matches_the_exact_source_checkout() -> None:
    """Label dependency-lock evidence with the exact PR source or push SHA."""
    workflow_text = _CI_PATH.read_text(encoding="utf-8")

    assert f"name: uv-lock-{_EXACT_SOURCE_SHA}" in workflow_text
    assert "name: uv-lock-${{ github.sha }}" not in workflow_text


def test_package_evidence_name_matches_the_exact_source_checkout() -> None:
    """Label package evidence with the exact PR source or push SHA."""
    workflow_text = _SUPPLY_CHAIN_PATH.read_text(encoding="utf-8")

    assert f"name: package-evidence-{_EXACT_SOURCE_SHA}" in workflow_text
    assert "name: package-evidence-${{ github.sha }}" not in workflow_text


def test_reproducibility_evidence_name_matches_the_exact_source_checkout() -> None:
    """Label reproducibility evidence with the exact PR source or push SHA."""
    workflow_text = _REPRODUCIBILITY_PATH.read_text(encoding="utf-8")

    assert f"name: reproducibility-{_EXACT_SOURCE_SHA}" in workflow_text
    assert "name: reproducibility-${{ github.sha }}" not in workflow_text


def test_package_smoke_covers_every_declared_conformance_profile() -> None:
    """Require installed-package CI to retain and enumerate every public profile."""
    workflow_text = _CI_PATH.read_text(encoding="utf-8")

    for profile_name in available_conformance_profile_names():
        resource_path = f'"cwl_context_contracts/conformance/{profile_name}"'
        assert resource_path in workflow_text, profile_name
        assert f'"{profile_name}",' in workflow_text, profile_name


def test_protected_main_revalidates_downloaded_evidence_before_attesting() -> None:
    """Never sign downloaded package bytes before their bundle is re-admitted."""
    workflow_text = _SUPPLY_CHAIN_PATH.read_text(encoding="utf-8")
    download_marker = "- name: Download exact-head package evidence"
    verify_marker = "- name: Verify downloaded package evidence before attestation"
    attest_marker = "- name: Attest SLSA build provenance"

    download_index = workflow_text.index(download_marker)
    verify_index = workflow_text.index(verify_marker)
    attest_index = workflow_text.index(attest_marker)

    assert download_index < verify_index < attest_index
    verification_step = workflow_text[verify_index:attest_index]
    assert "PYTHONPATH: src" in verification_step
    assert "verify_package_evidence_directory" in verification_step
    assert (
        "EXPECTED_PACKAGE_SNAPSHOT: "
        "${{ needs.package-evidence.outputs.package-snapshot }}"
        in verification_step
    )
    assert "package evidence changed since build verification" in verification_step


def test_receipt_smoke_uses_syft_spdx_package_version_field() -> None:
    """Keep the synthetic receipt SBOM compatible with the verified Syft wire shape."""
    workflow_text = _RECEIPT_PACKAGE_SMOKE_PATH.read_text(encoding="utf-8")

    assert '"software_packageVersion": "${package_version}"' in workflow_text
    assert '"packageVersion": "${package_version}"' not in workflow_text
