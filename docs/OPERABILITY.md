# Operability

## Scope

`context-graph-contracts` is a **stateless**, contract-only Python distribution. It does not run a broker, graph database, catalog, workflow engine, API service, or UI. Operational acceptance therefore means that an exact package can be installed, its schemas/contracts/fixtures can be loaded, every shipped semantic conformance profile can execute, the installed semantic evidence can be matched to an independently approved manifest, and the exact complete published JSON resource set can be retained and compared with independently approved byte-identity evidence without relying on repository source files.

## Installation acceptance

Use an immutable released version rather than a mutable branch. Before admitting it to a consumer environment:

1. Verify the release wheel or source distribution checksum against `SHA256SUMS` from the same exact source commit.
2. Verify the GitHub artifact attestation for the package before trusting its provenance.
3. Install into an isolated environment without editable/source-tree fallback.
4. Load every name returned by `available_schema_names()`, `available_contract_names()`, `available_fixture_names()`, and `available_conformance_profile_names()`.
5. Run the installed `cwl-context-conformance` command and require a passing report for every packaged semantic profile. A consumer implementation must also execute equivalent timestamp, context-assertion, CloudEvent, and CWL JSON vectors and fail closed when it cannot preserve the declared semantics.
6. Run installed `cwl-context-conformance-manifest` and retain its distribution version and exact profile SHA-256 digests with the deployment evidence.
7. Run installed `cwl-context-conformance-admit` against the independently approved manifest for the intended contract release; require exit `0`, `admitted=true`, passing `semantic_conformance`, and `manifest_verification.verified=true` before enabling the integration. This composite gate intentionally reruns installed semantics so an operator cannot accidentally check only profile bytes. Exit `1` means repair semantic drift or reconcile package/version/profile evidence. Exit `2` means repair the supplied manifest input. Approved-manifest input is read through the same fail-closed 1 MiB byte ceiling before UTF-8/JSON parsing used by `cwl-context-conformance-verify`. A positive admission proves the two deterministic contract gates only, not signature, organizational approval, artifact provenance, runtime authorization, or consumer-owned trust policy.
8. Run installed `cwl-context-bundle-manifest` and retain its distribution version plus the stable `resource_path`/SHA-256 identity for every explicitly published AsyncAPI document, JSON Schema, fixture, and semantic profile. A changed resource digest requires compatibility review and revalidation; the bundle manifest itself does not replace semantic execution, provenance, review, or runtime authorization.
9. Run installed `cwl-context-bundle-verify` against the complete bundle manifest independently approved for the intended release. Require exit `0`, `verified=true`, and an empty mismatch list. Exit `1` identifies package identity or exact missing/unexpected/digest-different resource drift; exit `2` means the approved bundle input is unreadable or invalid. Do not approve new bytes merely to clear a mismatch.

The CI package jobs are the executable reference for isolated installed-wheel acceptance and exercise the installed conformance runner, manifest generator, verifier, composite admission command, admission receipt, complete contract-bundle manifest, and approved complete-bundle verifier. The supply-chain workflow emits exact-head evidence under an artifact named `package-evidence-<commit-sha>` containing the built distributions, SPDX SBOM, and `SHA256SUMS`.

## Failure handling

Treat any of the following as non-passing: checksum mismatch, missing package resource, complete-resource manifest drift, unsupported conformance profile, failed negative vector, failed exact-value round trip, unknown truth-status promotion, inability to preserve tenant/provenance/time semantics, unreadable, oversized, or malformed approved-manifest input, package-version drift, profile-set drift, profile-digest drift, or complete-bundle missing/unexpected/digest-different resource evidence. Do not substitute a source checkout for a failed package, approve changed evidence merely to silence a mismatch, or promote inferred/proposed facts to authoritative truth as a recovery shortcut.

## Recovery

There is no owned persistent runtime state to restore. Recovery is package-oriented: select a previously accepted immutable version, verify its checksum and attestation again, install it cleanly, rerun the complete conformance suite, regenerate the installed conformance manifest and complete contract-bundle manifest, rerun composite semantic admission against the independently retained approved conformance manifest, and rerun complete-bundle verification against the independently retained approved bundle manifest for that exact version. Consumer-owned projections or databases remain the consumer product's recovery responsibility and must never be repaired by direct cross-service application-table SQL.

## Evidence retention

For a candidate release retain the exact source commit, dependency lock, wheel, source distribution, SPDX 3 SBOM, `SHA256SUMS`, provenance/SBOM attestations, installed conformance report, exact conformance manifest, complete contract-bundle manifest, approved conformance-manifest verification result, approved complete-bundle verification result, composite admission result, and the successful exact-head CI/security/review evidence required by live repository policy. A transient Actions artifact is build evidence, not by itself a published release or commercial-readiness claim, and a SHA-256 digest is byte-identity evidence rather than an authorization or signature claim.
