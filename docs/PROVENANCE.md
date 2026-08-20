# Build and Artifact Provenance

## Evidence model

The repository separates product-data provenance from software-build provenance. Context assertions use the provider-neutral provenance contract described by ADR 0005 and W3C PROV references. Released package provenance is separate supply-chain evidence proving which repository/workflow/commit produced a wheel or source distribution. Semantic conformance evidence is a third, narrower layer: it records whether the installed contract behavior passes the published vectors and which exact package version/profile bytes were tested. Complete contract-resource identity is another narrow evidence layer: it binds the installed distribution version to the exact packaged AsyncAPI, JSON Schema, fixture, and semantic-profile bytes and can be compared with independently approved complete-bundle evidence. Local package-evidence verification is another narrow layer: it recalculates the workflow-produced `SHA256SUMS`, requires the expected wheel/source/SBOM artifact set, refuses path/symlink substitution, and checks the SPDX 3.0.1 evidence shape. The full installed contract release-admission decision composes the semantic and complete-resource gates without converting either digest identity into provenance or trust. Complete release-evidence admission then composes that installed decision with the downloaded package-evidence decision and requires both to identify the same distribution version. None of these layers substitutes for protected-main provenance, independent review, release authorization, or another layer.

The `supply-chain` workflow is the executable baseline:

- build wheel and source distribution from the reviewed dependency lock;
- generate an **SPDX 3.0.1** JSON SBOM for the built distributions;
- generate and verify `SHA256SUMS` for wheel, source distribution, and SBOM;
- retain exact-head pull-request package evidence under `package-evidence-<commit-sha>`;
- on protected `main`, create **SLSA** build provenance and canonical SPDX 3 SBOM attestations with GitHub Actions OIDC-backed artifact attestations;
- because pinned `actions/attest` v4.2.2 auto-detects SPDX through SPDX 2.x `spdxVersion`/`SPDXID` fields, attest the canonical SPDX 3.0.1 JSON-LD through explicit in-toto custom-predicate mode (`https://spdx.dev/Document/v3`) instead of creating a second compatibility SBOM;
- immediately verify each wheel and source distribution against the exact repository, `refs/heads/main`, source SHA, signer workflow/digest, GitHub Actions OIDC issuer, and GitHub-hosted runner policy for both SLSA provenance and SPDX 3 predicates; and
- retain the machine-readable verification results under `attestation-verification-<commit-sha>` for release evidence review.

The workflow uses the SLSA provenance predicate family rather than treating a status label or PR description as provenance. The normative references are maintained in `docs/doctoring/REFERENCES.md`.

## Verification by a consumer

A buyer or downstream build should verify bytes, producer identity, and semantic evidence independently:

1. Download the exact package-evidence artifact and run `cwl-context-package-evidence-verify <evidence-directory>`. Exit `0` proves that the local wheel, source distribution, SPDX 3.0.1 SBOM, and `SHA256SUMS` agree and that the required evidence shape is present. It does **not** prove who produced those bytes.
2. Verify the **GitHub artifact attestation** for each wheel and source distribution against `ContextualWisdomLab/context-graph-contracts`, the intended protected-main source SHA/ref, and the expected signer workflow. Verify both the default SLSA provenance predicate and the `https://spdx.dev/Document/v3` predicate rather than accepting any attestation merely because a signature is valid.
3. Confirm the attested source repository, `refs/heads/main`, source digest, signer workflow/digest, GitHub Actions OIDC issuer, and hosted-runner provenance match the intended release evidence. The repository's protected-main workflow performs the same fail-closed checks and retains its JSON verifier results, but a consumer with its own trust policy should still verify independently.
4. Inspect the associated SPDX 3.0.1 SBOM and retain it with the accepted artifact.
5. Install the verified package and run `cwl-context-conformance`; cryptographic provenance does not prove semantic correctness or consumer compatibility by itself.
6. Capture `cwl-context-conformance-manifest` from that installed package and compare it with the independently approved manifest for the intended release using `cwl-context-conformance-verify`. A successful comparison proves the approved distribution version and semantic-profile bytes are installed; it does not prove who approved the manifest, who built the package, or whether the consumer is authorized to mutate any store.
7. Capture `cwl-context-bundle-manifest`, retain it with the accepted release evidence, and compare it with the independently approved complete-resource manifest using `cwl-context-bundle-verify`. Exit `0` proves exact distribution/resource identity equality only; any package, missing/unexpected resource, or digest mismatch requires resource-level review and compatibility revalidation rather than silent admission.
8. Run `cwl-context-release-admit <approved-conformance-manifest> <approved-contract-bundle-manifest>` so the installed semantic suite, approved semantic-profile identity, and approved complete-resource identity must all pass in one deterministic decision.
9. Run `cwl-context-release-evidence-admit <evidence-directory> <approved-conformance-manifest> <approved-contract-bundle-manifest>` before provenance acceptance. The command reruns the installed release admission and package-evidence verification together and fails closed when the verified wheel/source distribution version differs from the installed approved distribution version. Exit `0` is deterministic evidence consistency only; it does not verify the GitHub attestation, establish protected-main source identity, supply an independent approval, authorize publication, or grant runtime authority.

## Trust boundaries

- A GitHub Actions artifact without a protected-main release decision is build evidence, not a release.
- A successful local package-evidence verification proves only the consistency of the supplied evidence directory; it does not authenticate `SHA256SUMS` or bind the artifacts to a source commit.
- A checksum without trusted provenance can detect byte changes but cannot prove who produced the bytes.
- A conformance-profile or contract-resource SHA-256 digest proves byte identity only; it is not a signature or organizational approval.
- A matching approved conformance manifest or complete contract-bundle verification does not replace artifact provenance, independent review, semantic execution, or runtime authorization.
- A successful installed release-admission decision composes deterministic compatibility evidence only; it does not create protected-release eligibility, approval authority, artifact provenance, signature validity, or runtime authorization.
- A successful complete release-evidence admission additionally proves only that the verified package artifact set and the installed approved contract evidence name the same distribution version; it still does not prove who built or approved the bytes, bind them to protected `main`, verify an attestation, authorize publication, or grant runtime authority.
- A protected-main `gh attestation verify` pass proves that the selected signed statements satisfy the configured producer-identity policy for those exact subjects; it does not supply the human review or release authorization that made the source eligible for `main` in the first place.
- An attestation without semantic conformance does not prove the contracts behave as the buyer expects.
- An SBOM describes software composition; it is not a vulnerability-free or certification claim.
- This repository does not claim SLSA level, SOC 2, CSAP, or other certification merely because it emits provenance evidence.

## Retention and reproducibility

For each published version retain or link the exact source commit, immutable tag, reviewed dependency lock, release artifacts, SHA-256 digests, SPDX SBOM, local package-evidence verification result, provenance/SBOM attestations, exact protected-main attestation-verification JSON, installed conformance report, exact conformance manifest, approved-manifest verification result, complete contract-bundle manifest, approved complete-bundle verification result, installed release-admission result, complete release-evidence admission result, CI/security/review gate evidence, and release notes. Rebuilding should start from the exact source commit and lock; if rebuilt bytes differ, record that difference rather than substituting new bytes under the original version.
