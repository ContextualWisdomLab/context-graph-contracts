# ADR 0014: Verify package evidence without promoting checksums to provenance

## Status

Accepted for the stacked release-readiness slice. It is not protected-main shipped truth until the owning pull-request stack integrates through repository governance.

## Context

The supply-chain workflow already emits one wheel, one source distribution, an SPDX 3.0.1 SBOM, and `SHA256SUMS`, then verifies the checksums before uploading `package-evidence-${{ github.sha }}`. A buyer that downloads that artifact still needs an executable way to repeat the same byte-integrity checks before artifact-attestation and protected-release verification.

A checksum file is not a trust root. If an attacker can replace both an artifact and its checksum entry, local digest equality alone cannot identify the producer or source commit. GitHub artifact attestations, protected stable-branch policy, exact-current-head review, and release authorization therefore remain separate gates.

## Decision

Publish a small package-evidence verifier in the reference distribution.

The verifier:

1. accepts one local evidence directory only;
2. requires `SHA256SUMS` to name exactly one `cwl_context_contracts-*` wheel, one `cwl_context_contracts-*.tar.gz` source distribution, and `cwl-context-contracts.spdx.json`;
3. accepts only simple artifact basenames in the checksum manifest, rejecting traversal, duplicate names, malformed digests, and empty manifests;
4. refuses symlinked or missing required artifacts rather than following an external path;
5. recalculates SHA-256 for every required artifact and reports exact digest mismatches;
6. checks that the SBOM retains the repository workflow's SPDX 3.0.1 context, `CreationInfo` specification version, and a `software_Package` named `cwl-context-contracts`; and
7. emits deterministic machine-readable evidence plus the next required action.

The verifier does **not** accept a caller-supplied source commit as if that proved provenance. After local byte verification, the operator must verify artifact attestations against the intended repository and protected `main` source commit, then satisfy independent-review and release policy.

## Consequences

Consumers can repeat the package bundle's local integrity checks with the same installed toolchain used for semantic and complete-contract verification. Path traversal, symlink substitution, unrelated package substitution, checksum omission, checksum drift, and malformed SPDX evidence fail closed.

The tool intentionally cannot establish producer identity, attestation validity, independent approval, release eligibility, runtime authorization, or certification. Those remain outside the contract package's authority.

## Verification trace

- RED acceptance: `tests/test_package_evidence_verifier.py` was committed before the production verifier existed; security regressions additionally require the SPDX package identity and wheel/sdist distribution names to remain bound to `cwl-context-contracts`.
- GREEN implementation: `src/cwl_context_contracts/package_evidence_verifier.py`, public API export, and the `cwl-context-package-evidence-verify` entry point.
- Workflow alignment: `.github/workflows/supply-chain.yml` defines the same wheel/sdist/SPDX/SHA-256 evidence set and SPDX 3.0.1 baseline.
- Primary references: FIPS PUB 180-4 for SHA-256, SPDX 3.0.1 for the SBOM contract, and GitHub artifact-attestation documentation for the distinct producer-provenance verification step.

## References

GitHub. (n.d.). *Using artifact attestations to establish provenance for builds*. GitHub Docs. https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations

National Institute of Standards and Technology. (2015). *Secure Hash Standard (SHS)* (FIPS PUB 180-4). U.S. Department of Commerce. https://doi.org/10.6028/NIST.FIPS.180-4

SPDX Project. (2024). *SPDX specification* (Version 3.0.1). The Linux Foundation. https://spdx.github.io/spdx-spec/v3.0.1/
