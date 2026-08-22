"""Protect stable releases with exact GitHub artifact-attestation verification."""

from __future__ import annotations

from pathlib import Path

_SUPPLY_CHAIN_PATH = Path(".github/workflows/supply-chain.yml")
_SETUP_PYTHON = "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405"


def _protected_main_job(workflow_text: str) -> str:
    """Return the protected-main attestation job source."""
    return workflow_text.split("  attest-protected-main:\n", maxsplit=1)[1]


def _package_evidence_job(workflow_text: str) -> str:
    """Return the package-evidence job source before protected-main attestation."""
    jobs = workflow_text.split("  package-evidence:\n", maxsplit=1)[1]
    return jobs.split("  attest-protected-main:\n", maxsplit=1)[0]


def test_protected_main_invokes_executable_attestation_verifier() -> None:
    """Require the protected-main workflow to execute the regression-tested verifier."""
    workflow_text = _SUPPLY_CHAIN_PATH.read_text(encoding="utf-8")
    job = _protected_main_job(workflow_text)

    assert "name: Verify protected-main provenance and SBOM attestations" in job
    assert "SOURCE_SHA: ${{ github.sha }}" in job
    assert "SOURCE_REF: ${{ github.ref }}" in job
    assert "EXPECTED_SOURCE_REF: refs/heads/main" in job
    assert "REPOSITORY: ${{ github.repository }}" in job
    assert (
        "SIGNER_WORKFLOW: ${{ github.repository }}/.github/workflows/supply-chain.yml"
        in job
    )
    assert "SPDX_PREDICATE: https://spdx.dev/Document/v3" in job
    assert "EVIDENCE_DIR: evidence" in job
    assert "VERIFICATION_DIR: attestation-verification" in job
    assert "run: bash scripts/verify_release_attestations.sh" in job


def test_protected_main_binds_attestations_to_build_job_package_snapshot() -> None:
    """Carry the verified build-job package identity across the job trust boundary."""
    workflow_text = _SUPPLY_CHAIN_PATH.read_text(encoding="utf-8")
    package_job = _package_evidence_job(workflow_text)
    attestation_job = _protected_main_job(workflow_text)

    expected_output = (
        "package-snapshot: "
        "${{ steps.package-evidence-verification.outputs.package_snapshot }}"
    )
    output_write = 'echo "package_snapshot=$package_snapshot" >> "$GITHUB_OUTPUT"'
    expected_input = (
        "EXPECTED_PACKAGE_SNAPSHOT: "
        "${{ needs.package-evidence.outputs.package-snapshot }}"
    )
    assert expected_output in package_job
    assert "id: package-evidence-verification" in package_job
    assert output_write in package_job
    assert expected_input in attestation_job


def test_attested_package_bytes_are_in_the_reproducibility_comparison() -> None:
    """The exact package-evidence bytes must participate in double-build proof."""
    workflow_text = _SUPPLY_CHAIN_PATH.read_text(encoding="utf-8")
    package_job = _package_evidence_job(workflow_text)

    first_build = package_job.find("uv build --wheel --sdist --out-dir dist")
    witness_checkout = package_job.find("path: reproducibility-source")
    witness_build = package_job.find(
        "uv build --wheel --sdist --out-dir ../reproducibility-build"
    )
    comparison = package_job.find(
        "python scripts/verify_reproducible_package_builds.py "
        "dist reproducibility-build"
    )
    package_upload = package_job.find("name: Upload checked-out commit package evidence")

    assert "SOURCE_DATE_EPOCH: ${{ steps.source.outputs.source_date_epoch }}" in package_job
    assert min(first_build, witness_checkout, witness_build, comparison, package_upload) >= 0
    assert first_build < witness_checkout < witness_build < comparison < package_upload
    assert "name: package-reproducibility-${{ github.sha }}" in package_job


def test_protected_main_pins_python_before_python_backed_verification() -> None:
    """Do not rely on the mutable ubuntu-latest ambient Python installation."""
    workflow_text = _SUPPLY_CHAIN_PATH.read_text(encoding="utf-8")
    job = _protected_main_job(workflow_text)
    setup_offset = job.find(_SETUP_PYTHON)
    package_verify_offset = job.find("name: Verify downloaded package evidence")

    assert setup_offset >= 0
    assert package_verify_offset >= 0
    assert setup_offset < package_verify_offset
    assert 'python-version: "3.14"' in job[setup_offset:package_verify_offset]


def test_spdx3_attestation_uses_explicit_in_toto_predicate_mode() -> None:
    """Use explicit predicate mode for SPDX 3 JSON-LD attestations."""
    workflow_text = _SUPPLY_CHAIN_PATH.read_text(encoding="utf-8")
    attestation_step = workflow_text.split("- name: Attest SPDX SBOM", maxsplit=1)[1]
    attestation_step = attestation_step.split(
        "- name: Verify protected-main provenance and SBOM attestations",
        maxsplit=1,
    )[0]

    assert "sbom-path:" not in attestation_step
    assert "predicate-type: https://spdx.dev/Document/v3" in attestation_step
    assert (
        "predicate-path: evidence/cwl-context-contracts.spdx.json"
        in attestation_step
    )


def test_protected_main_retains_attestation_verification_records() -> None:
    """Keep machine-readable records for the exact stable source SHA."""
    workflow_text = _SUPPLY_CHAIN_PATH.read_text(encoding="utf-8")

    assert "name: attestation-verification-${{ github.sha }}" in workflow_text
    assert "path: attestation-verification/*.json" in workflow_text
    assert "retention-days: 90" in workflow_text
