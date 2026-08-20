# Release and Rollback

## Release invariant

A release may be cut only from one exact integrated **protected main** commit after the live repository policy and every applicable repository-owned gate pass together. A pull-request head, merge preview, mutable branch, predecessor-head check, skipped/neutral status, or transient build artifact is not release evidence.

Before tagging or publishing:

1. Re-fetch `main`, the live ruleset/branch protection, required workflows, review requirements, unresolved threads, and the exact integrated commit SHA.
2. Require exact-head Python 3.11–3.14 lint/test/100% statement-and-branch coverage, package smoke, semantic conformance, dependency-lock validation, security gates, and supply-chain evidence to be terminal success.
3. Install the built package into an isolated environment, run `cwl-context-conformance`, and require a passing report from the installed package rather than a source-tree import.
4. Run `cwl-context-conformance-manifest` from that same isolated installation and retain the exact distribution version plus every packaged semantic-profile SHA-256 digest with the release evidence. Then run `cwl-context-conformance-admit` against the independently approved manifest expected for the release and require exit `0`, `admitted=true`, a passing semantic report, and an exact manifest-verification result. This composite comparison proves installed semantic behavior plus package/version/profile byte identity only; it does not replace review, signature, provenance, SBOM, or authorization gates.
5. Require the protected-main supply-chain run to build the wheel and source distribution, generate the canonical SPDX 3.0.1 SBOM, generate `SHA256SUMS`, create SLSA provenance and explicit `https://spdx.dev/Document/v3` SBOM attestations for the exact package artifacts, and immediately verify both predicate classes for each wheel/source distribution against the exact repository, `refs/heads/main`, source SHA, signer workflow/digest, GitHub Actions OIDC issuer, and hosted-runner policy. Retain the machine-readable verification results under the exact source SHA.
6. Download that exact package-evidence bundle and run `cwl-context-release-evidence-admit <evidence-directory> <approved-conformance-manifest> <approved-contract-bundle-manifest>`. Require exit `0`, `admitted=true`, an exact installed semantic/complete-bundle admission, a passing wheel/source/SPDX/checksum verification, and equality between the verified package distribution version and the installed approved distribution version. This rejects evidence splicing across otherwise coherent release versions; it still does not authenticate the bundle or replace artifact attestation, protected-main source identity, independent review, or release authorization.
7. Independently verify the built wheel and source distribution attestations before publication even when the repository's protected-main verifier already passed. Require the intended repository/ref/source digest/signer identity for SLSA provenance and the canonical SPDX 3 predicate rather than accepting any valid signature or unrelated predicate.
8. Update `CHANGELOG.md` for the exact version and verify package metadata/version agree with the intended tag.
9. Publish/tag only after all preceding evidence still refers to the unchanged integrated commit. Record source and artifact SHA-256 digests, the exact conformance manifest, installed release-admission result, complete release-evidence admission result, retained attestation-verification JSON, and independent provenance/authorization evidence with the release.

This Git Flow repository may keep `develop` as its protected default integration branch. The release invariant is not satisfied until `main` is separately protected as the stable release branch by the intended organization governance and promotion from `develop` cannot become release evidence through an unreviewed or policy-bypassing mutation. Changing the default branch merely to make the release path look protected is not a remedy.

## Consumer admission

Consumers should pin an immutable compatible version. They must verify checksum and provenance, install the package rather than import from a mutable source checkout, retain the exact installed conformance manifest, and run `cwl-context-release-evidence-admit` against the independently approved conformance and complete-bundle manifests plus the exact downloaded package-evidence directory before accepting Context Fabric data. The composed command reruns installed semantic and complete-resource admission, verifies package evidence, and requires the same distribution version across those layers so neither evidence path can be accidentally spliced or omitted. A positive admission remains only deterministic contract/evidence consistency; it is not a grant of runtime authority and is not a substitute for artifact attestation, protected-release evidence, independent approval, or consumer authorization policy.

## Rollback

Rollback is package-version rollback because this repository owns no persistent application database or mutable runtime state:

1. Stop promotion of the suspect version; do not rewrite or delete the original release evidence.
2. Select the most recent previously accepted immutable version compatible with the consumer.
3. Re-verify its `SHA256SUMS`, SLSA provenance attestation, and SPDX 3 attestation against the exact original protected-main source/signer identity.
4. Reinstall that exact version into a clean environment.
5. Regenerate its installed conformance and complete-bundle manifests and rerun `cwl-context-release-evidence-admit` against the previously approved manifests and retained package-evidence directory for that exact rollback version.
6. Rerun consumer compatibility acceptance and authorization checks.
7. Record which consumers moved back, the reason, previous/current artifact digests, conformance/bundle manifest identities, complete release-evidence admission results, attestation-verification evidence, and the corrective issue/PR.

Do not force-move a tag, replace published artifacts under the same version, weaken conformance, approve a changed manifest merely to make rollback pass, splice evidence from another distribution version, accept an attestation for a different source/signer identity, or mutate consumer databases to simulate a package rollback. A corrected incompatible contract requires a new version and explicit compatibility/migration evidence.

## Migration semantics

The initial contract package has no owned database migration. Contract evolution is schema/package evolution: compatibility must be explicit, old meanings cannot be silently reassigned, and consumers control migration of their own authoritative data. When a future change requires consumer data adaptation, document the old/new contract versions, deterministic transformation, failure/rollback behavior, and conformance vectors before release.
