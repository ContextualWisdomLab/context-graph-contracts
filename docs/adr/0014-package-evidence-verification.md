# ADR 0014: Verify package evidence without promoting checksums to provenance

## Status

Accepted for the stacked release-readiness slice. It is not protected-main shipped truth until the owning pull-request stack integrates through repository governance.

## Context

The supply-chain workflow already emits one wheel, one source distribution, an SPDX 3.0.1 SBOM, and `SHA256SUMS`, then verifies the checksums before uploading `package-evidence-${{ github.sha }}`. A buyer that downloads that artifact still needs an executable way to repeat the same byte-integrity checks before artifact-attestation and protected-release verification.

A checksum file is not a trust root. If an attacker can replace both an artifact and its checksum entry, local digest equality alone cannot identify the producer or source commit. GitHub artifact attestations, protected stable-branch policy, exact-current-head review, and release authorization therefore remain separate gates.

Downloaded evidence is also untrusted parser input. RFC 8259 permits receivers to impose implementation limits, says interoperable object names should be unique because duplicate-member handling differs across implementations, and excludes non-finite values such as `NaN` and `Infinity` from the JSON number grammar. The release verifier must not let Python-specific parser extensions or unbounded metadata reads turn package evidence into ambiguous or resource-exhausting input.

## Decision

Publish a small package-evidence verifier in the reference distribution.

The verifier:

1. accepts one local evidence directory only;
2. requires `SHA256SUMS` to name exactly one `cwl_context_contracts-*` wheel, one `cwl_context_contracts-*.tar.gz` source distribution, and `cwl-context-contracts.spdx.json`, with the wheel and source distribution carrying the same release version;
3. accepts only simple artifact basenames in the checksum manifest, rejecting traversal, duplicate names, malformed digests, and empty manifests;
4. refuses symlinked or missing required artifacts rather than following an external path;
5. requires the evidence directory's top-level wheel/source-distribution set to equal the installable artifact set declared by `SHA256SUMS`, so an additional unchecksummed wheel or source distribution cannot inherit a successful verification result;
6. bounds `SHA256SUMS` at 64 KiB and SPDX JSON at 16 MiB plus one sentinel byte, requires UTF-8 text, rejects duplicate JSON object members and Python-only non-finite numeric constants, converts package-directory listing failures into deterministic `evidence_directory_unreadable` input evidence, and converts post-check artifact read failures into deterministic `artifact_unreadable:<name>` evidence instead of allowing an I/O exception to escape;
7. recalculates SHA-256 for every readable required artifact and reports exact digest mismatches;
8. checks that the SBOM retains the repository workflow's SPDX 3.0.1 context, `CreationInfo` specification version, and exactly one `software_Package` named `cwl-context-contracts` whose Syft SPDX 3 JSON-LD `software_packageVersion` equals the wheel/source release version; and
9. emits deterministic machine-readable evidence plus the next required action.

The verifier does **not** accept a caller-supplied source commit as if that proved provenance. After local byte verification, the operator must verify artifact attestations against the intended repository and protected `main` source commit, then satisfy independent-review and release policy.

## Consequences

Consumers can repeat the package bundle's local integrity checks with the same installed toolchain used for semantic and complete-contract verification. Path traversal, symlink substitution, unrelated package substitution, mixed release versions, SBOM-to-artifact version drift, checksum omission, checksum drift, an unlisted installable package artifact, unreadable package-directory enumeration, malformed or ambiguous JSON, non-portable non-finite numeric constants, oversized metadata, post-check artifact read failure, and malformed SPDX evidence fail closed.

The byte ceilings are evidence-envelope limits, not size claims about the Python package itself. They intentionally bound only the checksum manifest and parsed SPDX metadata; wheel and source-distribution payloads are SHA-256 streamed in 1 MiB chunks rather than loaded wholesale. A future legitimate SPDX document that exceeds the bound requires an explicit reviewed contract change instead of silently increasing parser exposure.

The tool intentionally cannot establish producer identity, attestation validity, independent approval, release eligibility, runtime authorization, or certification. Those remain outside the contract package's authority.

## Verification trace

- RED acceptance: `tests/test_package_evidence_verifier.py` was committed before the production verifier existed; security regressions additionally require the SPDX package identity and exact `software_packageVersion` to remain bound to the coherent wheel/sdist release version and reject installable artifacts omitted from `SHA256SUMS`.
- Hostile-input RED acceptance: `tests/test_package_evidence_verifier_input_bounds.py` covers duplicate JSON members, `NaN`, invalid UTF-8, checksum/SBOM size ceilings, post-check artifact read failure, and post-digest SBOM disappearance; `tests/test_package_evidence_verifier_security.py` additionally covers package-directory listing failure as a stable input error.
- GREEN implementation: `src/cwl_context_contracts/package_evidence_verifier.py`, public API export, and the `cwl-context-package-evidence-verify` entry point.
- Workflow alignment: `.github/workflows/supply-chain.yml` defines the same wheel/sdist/SPDX/SHA-256 evidence set and SPDX 3.0.1 baseline; installed-wheel smoke emits the exact installed distribution version into Syft's SPDX 3 JSON-LD `software_packageVersion` field.
- Primary references: RFC 8259 §§4 and 6 for interoperable JSON object/numeric behavior, FIPS PUB 180-4 for SHA-256, SPDX 3.0.1 for the SBOM contract, and GitHub artifact-attestation documentation for the distinct producer-provenance verification step.

## References

Bray, T. (Ed.). (2017). *The JavaScript Object Notation (JSON) Data Interchange Format* (RFC 8259). Internet Engineering Task Force. https://doi.org/10.17487/RFC8259

GitHub. (n.d.). *Using artifact attestations to establish provenance for builds*. GitHub Docs. https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations

National Institute of Standards and Technology. (2015). *Secure Hash Standard (SHS)* (FIPS PUB 180-4). U.S. Department of Commerce. https://doi.org/10.6028/NIST.FIPS.180-4

SPDX Project. (2024). *SPDX specification* (Version 3.0.1). The Linux Foundation. https://spdx.github.io/spdx-spec/v3.0.1/
