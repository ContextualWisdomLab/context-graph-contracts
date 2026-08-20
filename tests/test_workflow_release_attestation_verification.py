"""Protect stable releases with exact GitHub artifact-attestation verification."""

from __future__ import annotations

from pathlib import Path

_SUPPLY_CHAIN_PATH = Path(".github/workflows/supply-chain.yml")


def test_protected_main_verifies_provenance_and_spdx3_attestations() -> None:
    """Require exact protected-main source and signer identity for package attestations."""
    workflow_text = _SUPPLY_CHAIN_PATH.read_text(encoding="utf-8")

    assert "name: Verify protected-main provenance and SBOM attestations" in workflow_text
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
