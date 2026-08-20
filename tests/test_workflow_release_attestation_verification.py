"""Protect stable releases with exact GitHub artifact-attestation verification."""

from __future__ import annotations

from pathlib import Path

_SUPPLY_CHAIN_PATH = Path(".github/workflows/supply-chain.yml")


def test_protected_main_verifies_provenance_and_spdx3_attestations() -> None:
    """Require exact protected-main source and signer identity."""
    workflow_text = _SUPPLY_CHAIN_PATH.read_text(encoding="utf-8")

    assert (
        "name: Verify protected-main provenance and SBOM attestations"
        in workflow_text
    )
    assert 'SOURCE_SHA: ${{ github.sha }}' in workflow_text
    assert 'SOURCE_REF: ${{ github.ref }}' in workflow_text
    assert 'EXPECTED_SOURCE_REF: refs/heads/main' in workflow_text
    assert (
        'SIGNER_WORKFLOW: ContextualWisdomLab/context-graph-contracts/'
        '.github/workflows/supply-chain.yml'
    ) in workflow_text
    assert 'REPOSITORY: ContextualWisdomLab/context-graph-contracts' in workflow_text
    assert 'SPDX_PREDICATE: https://spdx.dev/Document/v3' in workflow_text
    assert '--source-digest "$SOURCE_SHA"' in workflow_text
    assert '--source-ref "$EXPECTED_SOURCE_REF"' in workflow_text
    assert '--signer-digest "$SOURCE_SHA"' in workflow_text
    assert '--signer-workflow "$SIGNER_WORKFLOW"' in workflow_text
    assert '--repo "$REPOSITORY"' in workflow_text
    assert '--deny-self-hosted-runners' in workflow_text
    assert '--predicate-type "$SPDX_PREDICATE"' in workflow_text
    assert 'if [[ "$SOURCE_REF" != "$EXPECTED_SOURCE_REF" ]]' in workflow_text
    assert 'artifacts=(evidence/*.whl evidence/*.tar.gz)' in workflow_text
    assert 'if (( ${#artifacts[@]} != 2 )); then' in workflow_text
    assert workflow_text.count('gh attestation verify "$artifact"') == 2


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

    assert "mkdir -p attestation-verification" in workflow_text
    assert (
        'attestation-verification/$(basename "$artifact").provenance.json'
        in workflow_text
    )
    assert (
        'attestation-verification/$(basename "$artifact").sbom.json'
        in workflow_text
    )
    assert "name: attestation-verification-${{ github.sha }}" in workflow_text
    assert "path: attestation-verification/*.json" in workflow_text
    assert "retention-days: 90" in workflow_text
