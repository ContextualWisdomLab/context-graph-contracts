# Release and Rollback

## Release invariant

A release may be cut only from one exact integrated **protected main** commit after the live repository policy and every applicable repository-owned gate pass together. A pull-request head, merge preview, mutable branch, predecessor-head check, skipped/neutral status, or transient build artifact is not release evidence.

Before tagging or publishing:

1. Re-fetch `main`, the live ruleset/branch protection, required workflows, review requirements, unresolved threads, and the exact integrated commit SHA.
2. Require exact-head Python 3.11–3.14 lint/test/100% statement-and-branch coverage, package smoke, semantic conformance, dependency-lock validation, security gates, and supply-chain evidence to be terminal success.
3. Install the built package into an isolated environment, run `cwl-context-conformance`, and require a passing report from the installed package rather than a source-tree import.
4. Run `cwl-context-conformance-manifest` from that same isolated installation and retain the exact distribution version plus every packaged semantic-profile SHA-256 digest with the release evidence. Then run `cwl-context-conformance-admit` against the independently approved manifest expected for the release and require exit `0`, `admitted=true`, a passing semantic report, and an exact manifest-verification result. This composite comparison proves installed semantic behavior plus package/version/profile byte identity only; it does not replace review, signature, provenance, SBOM, or authorization gates.
5. Require the protected-main supply-chain run to build the wheel and source distribution, generate the SPDX 3.0.1 SBOM, generate `SHA256SUMS`, and create provenance/SBOM attestations for the exact artifacts.
6. Verify the built files against `SHA256SUMS` and verify their GitHub attestations before publication.
7. Update `CHANGELOG.md` for the exact version and verify package metadata/version agree with the intended tag.
8. Publish/tag only after all preceding evidence still refers to the unchanged integrated commit. Record source and artifact SHA-256 digests, the exact conformance manifest, the composite admission result, and independent provenance/authorization evidence with the release.

This Git Flow repository may keep `develop` as its protected default integration branch. The release invariant is not satisfied until `main` is separately protected as the stable release branch by the intended organization governance and promotion from `develop` cannot become release evidence through an unreviewed or policy-bypassing mutation. Changing the default branch merely to make the release path look protected is not a remedy.

## Consumer admission

Consumers should pin an immutable compatible version. They must verify checksum and provenance, install the package rather than import from a mutable source checkout, retain the exact installed conformance manifest, and run `cwl-context-conformance-admit` against the independently approved manifest for that consumer/release before accepting Context Fabric data. The composite command reruns every packaged semantic profile and verifies exact approved profile bytes so neither gate can be accidentally omitted. A positive admission remains only deterministic contract evidence; it is not a grant of runtime authority and is not a substitute for artifact attestation, independent approval, or consumer authorization policy.

## Rollback

Rollback is package-version rollback because this repository owns no persistent application database or mutable runtime state:

1. Stop promotion of the suspect version; do not rewrite or delete the original release evidence.
2. Select the most recent previously accepted immutable version compatible with the consumer.
3. Re-verify its `SHA256SUMS` and GitHub artifact attestation.
4. Reinstall that exact version into a clean environment.
5. Regenerate its installed conformance manifest and rerun `cwl-context-conformance-admit` against the previously approved manifest for that exact rollback version.
6. Rerun consumer compatibility acceptance and authorization checks.
7. Record which consumers moved back, the reason, previous/current artifact digests, conformance-manifest identities, admission results, and the corrective issue/PR.

Do not force-move a tag, replace published artifacts under the same version, weaken conformance, approve a changed manifest merely to make rollback pass, or mutate consumer databases to simulate a package rollback. A corrected incompatible contract requires a new version and explicit compatibility/migration evidence.

## Migration semantics

The initial contract package has no owned database migration. Contract evolution is schema/package evolution: compatibility must be explicit, old meanings cannot be silently reassigned, and consumers control migration of their own authoritative data. When a future change requires consumer data adaptation, document the old/new contract versions, deterministic transformation, failure/rollback behavior, and conformance vectors before release.
