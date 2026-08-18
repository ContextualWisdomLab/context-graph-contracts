# Build and Artifact Provenance

## Evidence model

The repository separates product-data provenance from software-build provenance. Context assertions use the provider-neutral provenance contract described by ADR 0005 and W3C PROV references. Released package provenance is separate supply-chain evidence proving which repository/workflow/commit produced a wheel or source distribution. Semantic conformance evidence is a third, narrower layer: it records whether the installed contract behavior passes the published vectors and which exact package version/profile bytes were tested. Complete contract-resource identity is another narrow evidence layer: it binds the installed distribution version to the exact packaged AsyncAPI, JSON Schema, fixture, and semantic-profile bytes and can be compared with independently approved complete-bundle evidence. None of these layers substitutes for another.

The `supply-chain` workflow is the executable baseline:

- build wheel and source distribution from the reviewed dependency lock;
- generate an **SPDX 3.0.1** JSON SBOM for the built distributions;
- generate and verify `SHA256SUMS` for wheel, source distribution, and SBOM;
- retain exact-head pull-request package evidence under `package-evidence-<commit-sha>`;
- on protected `main`, create **SLSA** build provenance and SBOM attestations with GitHub Actions OIDC-backed artifact attestations.

The workflow uses the SLSA provenance predicate family rather than treating a status label or PR description as provenance. The normative references are maintained in `docs/doctoring/REFERENCES.md`.

## Verification by a consumer

A buyer or downstream build should verify bytes, producer identity, and semantic evidence independently:

1. Compare the downloaded wheel/source distribution SHA-256 digest with the release's `SHA256SUMS`.
2. Verify the **GitHub artifact attestation** for each executable/installable artifact against `ContextualWisdomLab/context-graph-contracts`, using GitHub's supported attestation verifier (for example `gh attestation verify <artifact> -R ContextualWisdomLab/context-graph-contracts`).
3. Confirm the attested source repository, workflow identity, and commit SHA equal the intended protected-main release evidence.
4. Inspect the associated SPDX 3.0.1 SBOM and retain it with the accepted artifact.
5. Install the verified package and run `cwl-context-conformance`; cryptographic provenance does not prove semantic correctness or consumer compatibility by itself.
6. Capture `cwl-context-conformance-manifest` from that installed package and compare it with the independently approved manifest for the intended release using `cwl-context-conformance-verify`. A successful comparison proves the approved distribution version and semantic-profile bytes are installed; it does not prove who approved the manifest, who built the package, or whether the consumer is authorized to mutate any store.
7. Capture `cwl-context-bundle-manifest`, retain it with the accepted release evidence, and compare it with the independently approved complete-resource manifest using `cwl-context-bundle-verify`. Exit `0` proves exact distribution/resource identity equality only; any package, missing/unexpected resource, or digest mismatch requires resource-level review and compatibility revalidation rather than silent admission.

## Trust boundaries

- A GitHub Actions artifact without a protected-main release decision is build evidence, not a release.
- A checksum without trusted provenance can detect byte changes but cannot prove who produced the bytes.
- A conformance-profile or contract-resource SHA-256 digest proves byte identity only; it is not a signature or organizational approval.
- A matching approved conformance manifest or complete contract-bundle verification does not replace artifact provenance, independent review, semantic execution, or runtime authorization.
- An attestation without semantic conformance does not prove the contracts behave as the buyer expects.
- An SBOM describes software composition; it is not a vulnerability-free or certification claim.
- This repository does not claim SLSA level, SOC 2, CSAP, or other certification merely because it emits provenance evidence.

## Retention and reproducibility

For each published version retain or link the exact source commit, immutable tag, reviewed dependency lock, release artifacts, SHA-256 digests, SPDX SBOM, provenance/SBOM attestations, installed conformance report, exact conformance manifest, approved-manifest verification result, complete contract-bundle manifest, approved complete-bundle verification result, CI/security/review gate evidence, and release notes. Rebuilding should start from the exact source commit and lock; if rebuilt bytes differ, record that difference rather than substituting new bytes under the original version.
