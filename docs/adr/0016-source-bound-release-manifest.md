# ADR 0016: Bind release package evidence to protected source with an attested manifest

- Status: Proposed
- Date: 2026-09-02
- Owners: Context Graph Contracts Shared Kernel
- Supersedes: none
- Depends on: ADR 0014, ADR 0015

## Context

The release-evidence stack can prove that one wheel, one source distribution and one SPDX document form a coherent same-version package bundle, and the protected-main workflow can independently verify GitHub artifact attestations for those package bytes. A consumer still needs one portable release artifact that says which exact package digests, protected source revision and signer workflow belong together.

A bare `release_commit_sha` in a consumer repository does not solve that problem. It is caller-controlled metadata unless the consumer can authenticate evidence that binds the exact package bytes to that source revision. GitHub's attestation guidance is explicit that generation alone provides no security benefit; consumers must verify the attestation, its subject and signer identity. The GitHub CLI additionally distinguishes source repository digest/ref from signer workflow identity and supports enforcing all of them during `gh attestation verify`. SLSA likewise defines provenance as verifiable information tracing an artifact back to its source and build process, not as an unsigned claim stored beside the artifact.

The Shared Kernel must solve this interoperability problem without becoming a release authority, workflow engine, package registry, EA database or application runtime.

## Decision drivers and constraints

1. Package byte identity, source identity and consumer authorization remain separate facts.
2. The source repository is `ContextualWisdomLab/context-graph-contracts`; the intended protected release ref is `refs/heads/main`.
3. The package evidence entering this step must already be the strict verified wheel/source/SPDX snapshot from the existing release-evidence verifier.
4. A generated JSON manifest is not trusted merely because it contains hashes or a commit SHA.
5. The manifest must be portable to consumers and independently verifiable with ordinary GitHub/Sigstore tooling.
6. Untrusted manifest inputs must be bounded, strict UTF-8 JSON and fail closed on duplicate members, non-standard numbers, excessive size or depth, malformed artifact identity, mixed versions or unauthorized source identity.
7. No consumer is allowed to promote foreign analysis, malware verdict, risk score or product truth through this release mechanism.

## Considered alternatives

### A. Keep only `release_commit_sha` in each consumer

Rejected. Shape-checking a 40-hex string establishes syntax only. It does not prove that the installed wheel, complete contract bundle or SBOM came from that revision.

### B. Treat the existing package checksum snapshot as provenance

Rejected. SHA-256 equality establishes byte identity, not signer/source authenticity. It would collapse deterministic package consistency into a trust claim that belongs to the attestation verifier.

### C. Encode source revision directly into domain schemas or Context Assertion

Rejected. Release mechanics are not Context Fabric domain truth. Doing so would make vendor/repository mechanics part of the Shared Kernel's business interchange contracts and would leak release concerns into all producers and consumers.

### D. Emit one release-source manifest and authenticate that manifest independently

Selected. The manifest is a compact digest-bound release evidence artifact. The protected-main workflow first re-verifies package provenance and SPDX attestations, then creates the manifest, attests the manifest itself, and verifies that attestation against the same repository, protected ref, exact source digest, signer digest/workflow, GitHub Actions OIDC issuer, hosted-runner policy and SLSA predicate before retaining the evidence.

## Decision

Publish `cwl-context-release-source-manifest/v1` as release evidence, not application authority.

The manifest binds:

- distribution name and semantic version;
- immutable release tag;
- exact repository, `refs/heads/main` and 40-hex source revision;
- exact signer workflow identity;
- SHA-256 of the canonical verified package-evidence snapshot; and
- exact SHA-256 identities of the wheel, source distribution and SPDX document.

Manifest generation accepts only an already-positive `cwl-context-package-evidence-verification/v1` snapshot. The CLI boundary reads at most 1 MiB, requires UTF-8, caps JSON structural depth at 64, rejects duplicate object members and non-standard JSON constants, and requires one same-version wheel/source pair plus the exact SPDX artifact.

The manifest is then an artifact subject of a separate GitHub SLSA provenance attestation. Release automation must verify that attestation before retaining or publishing the manifest. Consumers must independently authenticate the released manifest or its attestation bundle and must match the manifest's exact package/version/contract evidence to what they actually install. A copied manifest or a matching JSON shape is non-authoritative evidence.

This ADR remains **Proposed** until the code reaches protected integration and an immutable release proves the end-to-end path. An open PR, queued workflow or local fixture is not acceptance evidence.

## Consequences

### Positive

- EA and other consumers receive a stable source/package binding without copying CGC implementation or reading its repository database.
- Source authenticity is delegated to cryptographically verified artifact attestations rather than inferred from caller metadata.
- Exact package, source, signer and release identities remain auditable as separate values.
- The Shared Kernel remains contract-only; release evidence does not acquire foreign product authority.

### Costs and risks

- A consumer must perform or rely on an independently governed attestation verification step; checking the manifest alone is insufficient.
- The workflow that signs the manifest remains part of the trusted source policy. Consumers should pin signer workflow/source identity and audit changes to that workflow.
- GitHub CLI/Sigstore behavior is an external release-tooling dependency. The manifest format itself remains provider-neutral evidence, but GitHub-specific signing/verification mechanics stay in release automation and documentation rather than domain schemas.
- No immutable release exists at the time of this decision. EA must continue to fail closed until released evidence exists.

## Verification and follow-up

- Unit and hostile tests cover exact artifact/version/source binding, malformed evidence, duplicate JSON members, non-standard constants, UTF-8, 1 MiB size and 64-level depth limits.
- Workflow fitness tests require package attestation verification before manifest generation, manifest attestation before manifest verification, and retention only after successful verification.
- Protected-main execution must produce actual runner assignment, checkout SHA, package attestations, manifest attestation and verification evidence on the unchanged source head.
- The first consumer integration must verify the released manifest/attestation rather than merely adding a commit-SHA field.
- `docs/product-technical-gap-baseline.md`, release documentation and consumer handoffs must remain explicit that no open PR or self-asserted manifest is released authority.

## References

GitHub, Inc. (n.d.). *Artifact attestations*. GitHub Docs. Retrieved September 2, 2026, from https://docs.github.com/en/actions/concepts/security/artifact-attestations

GitHub, Inc. (n.d.). *gh attestation verify*. GitHub CLI manual. Retrieved September 2, 2026, from https://cli.github.com/manual/gh_attestation_verify

Open Source Security Foundation. (2026). *SLSA specification, version 1.2: Provenance*. https://slsa.dev/spec/v1.2/provenance
