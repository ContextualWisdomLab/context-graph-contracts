# Release and Rollback

## Release invariant

A release may be cut only from one exact integrated **protected main** commit after the live repository policy and every applicable repository-owned gate pass together. A pull-request head, merge preview, mutable branch, predecessor-head check, skipped/neutral status, or transient build artifact is not release evidence.

Before tagging or publishing:

1. Re-fetch `main`, the live ruleset/branch protection, required workflows, review requirements, unresolved threads, and the exact integrated commit SHA.
2. Require exact-head Python 3.11–3.14 lint/test/100% statement-and-branch coverage, package smoke, semantic conformance, dependency-lock validation, security gates, and supply-chain evidence to be terminal success.
3. Require the protected-main supply-chain run to build the wheel and source distribution, generate the SPDX 3.0.1 SBOM, generate `SHA256SUMS`, and create provenance/SBOM attestations for the exact artifacts.
4. Verify the built files against `SHA256SUMS` and verify their GitHub attestations before publication.
5. Update `CHANGELOG.md` for the exact version and verify package metadata/version agree with the intended tag.
6. Publish/tag only after all preceding evidence still refers to the unchanged integrated commit. Record source and artifact SHA-256 digests with the release.

Until repository metadata identifies `main` as the protected default branch and the intended organization governance applies to it, the release invariant is not satisfied.

## Consumer admission

Consumers should pin an immutable compatible version. They must verify checksum and provenance, install the package rather than import from a mutable source checkout, then execute every packaged semantic conformance profile before accepting Context Fabric data.

## Rollback

Rollback is package-version rollback because this repository owns no persistent application database or mutable runtime state:

1. Stop promotion of the suspect version; do not rewrite or delete the original release evidence.
2. Select the most recent previously accepted immutable version compatible with the consumer.
3. Re-verify its `SHA256SUMS` and GitHub artifact attestation.
4. Reinstall that exact version into a clean environment.
5. Rerun the complete installed-package conformance suite and consumer compatibility acceptance.
6. Record which consumers moved back, the reason, previous/current artifact digests, and the corrective issue/PR.

Do not force-move a tag, replace published artifacts under the same version, weaken conformance, or mutate consumer databases to simulate a package rollback. A corrected incompatible contract requires a new version and explicit compatibility/migration evidence.

## Migration semantics

The initial contract package has no owned database migration. Contract evolution is schema/package evolution: compatibility must be explicit, old meanings cannot be silently reassigned, and consumers control migration of their own authoritative data. When a future change requires consumer data adaptation, document the old/new contract versions, deterministic transformation, failure/rollback behavior, and conformance vectors before release.
