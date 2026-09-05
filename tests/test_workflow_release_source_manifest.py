"""Workflow fitness tests for source-bound release manifest provenance."""

from __future__ import annotations

from pathlib import Path

_SUPPLY_CHAIN = Path(".github/workflows/supply-chain.yml")


def _protected_main_job() -> str:
    """Return only the protected-main attestation job source."""
    workflow = _SUPPLY_CHAIN.read_text(encoding="utf-8")
    return workflow.split("  attest-protected-main:\n", maxsplit=1)[1]


def test_source_manifest_is_built_only_after_package_attestation_verification() -> None:
    """Do not mint source evidence before exact package attestations are verified."""
    job = _protected_main_job()
    package_verify = job.find(
        "name: Verify protected-main provenance and SBOM attestations"
    )
    manifest_build = job.find("name: Build attestable release-source manifest")
    manifest_attest = job.find("name: Attest release-source manifest")
    manifest_verify = job.find("name: Verify release-source manifest provenance")
    retain = job.find("name: Retain protected-main attestation verification evidence")

    positions = (
        package_verify,
        manifest_build,
        manifest_attest,
        manifest_verify,
        retain,
    )
    assert min(positions) >= 0
    assert package_verify < manifest_build < manifest_attest < manifest_verify < retain


def test_source_manifest_uses_exact_package_snapshot_and_protected_identity() -> None:
    """Manifest generation binds one downloaded package snapshot to protected main."""
    job = _protected_main_job()
    build_step = job.split(
        "- name: Build attestable release-source manifest",
        maxsplit=1,
    )[1].split("- name: Attest release-source manifest", maxsplit=1)[0]

    assert "evidence/package-evidence-verification.json" in build_step
    assert "SOURCE_SHA: ${{ github.sha }}" in build_step
    assert "SOURCE_REF: ${{ github.ref }}" in build_step
    assert "REPOSITORY: ${{ github.repository }}" in build_step
    assert (
        "SIGNER_WORKFLOW: ${{ github.repository }}/.github/workflows/supply-chain.yml"
        in build_step
    )
    assert '--source-repository "$REPOSITORY"' in build_step
    assert '--source-ref "$SOURCE_REF"' in build_step
    assert '--source-sha "$SOURCE_SHA"' in build_step
    assert '--signer-workflow "$SIGNER_WORKFLOW"' in build_step


def test_source_manifest_itself_is_attested_and_verified_against_same_source() -> None:
    """A self-asserted JSON manifest never becomes release provenance by itself."""
    job = _protected_main_job()
    attest_step = job.split(
        "- name: Attest release-source manifest",
        maxsplit=1,
    )[1].split("- name: Verify release-source manifest provenance", maxsplit=1)[0]
    verify_step = job.split(
        "- name: Verify release-source manifest provenance",
        maxsplit=1,
    )[1].split(
        "- name: Retain protected-main attestation verification evidence",
        maxsplit=1,
    )[0]

    manifest_path = "attestation-verification/release-source-manifest.json"
    assert f"subject-path: {manifest_path}" in attest_step
    assert f'manifest_path="{manifest_path}"' in verify_step
    assert '--repo "$REPOSITORY"' in verify_step
    assert '--source-digest "$SOURCE_SHA"' in verify_step
    assert '--source-ref "$EXPECTED_SOURCE_REF"' in verify_step
    assert '--signer-digest "$SOURCE_SHA"' in verify_step
    assert '--signer-workflow "$SIGNER_WORKFLOW"' in verify_step
    assert "--deny-self-hosted-runners" in verify_step
    assert "--predicate-type https://slsa.dev/provenance/v1" in verify_step
    assert "release-source-manifest.provenance.json" in verify_step
