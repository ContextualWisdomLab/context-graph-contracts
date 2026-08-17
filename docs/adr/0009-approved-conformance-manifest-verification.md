# ADR 0009: Verify installed conformance evidence against an approved manifest

- Status: Accepted
- Date: 2026-08-17

## Context

ADR 0008 makes the installed distribution version and exact semantic-profile bytes machine-readable, but generation alone still leaves a buyer or consuming service to compare that evidence manually with the contract release it approved. Manual comparison is an avoidable fail-open integration risk: a compatible-looking package name can carry a different version, a published profile can drift under the same file name, a profile can be absent, or an unapproved profile can appear.

The comparison belongs in the contract package because the package owns the manifest format and packaged semantic resources. Approval authority does not belong here. A verifier must therefore answer only whether the installed evidence matches an independently supplied approved manifest, and it must remain deterministic, offline, provider-neutral, and unable to promote its own output into organizational trust.

## Decision

Publish `verify_packaged_conformance_manifest()` and the installed `cwl-context-conformance-verify` command. The verifier:

1. rebuilds the installed `cwl-context-conformance-manifest/v1` evidence from the installed distribution;
2. compares the approved manifest's format, distribution name/version, hash algorithm, profile count, profile names, and SHA-256 values with the installed evidence;
3. fails closed on missing, unexpected, duplicate, malformed, or digest-different profile evidence;
4. returns stable mismatch identities so automation can distinguish package-version drift from a specific semantic-profile drift;
5. returns an explicit next action: accept exact evidence only on a full match, otherwise install the approved package or approve a newly reviewed exact manifest;
6. uses exit `0` for a verified match, exit `1` for evidence drift, and exit `2` for an unreadable or invalid approved-manifest input;
7. does not decide who may approve a manifest and does not replace signatures, SBOMs, protected-build provenance, independent review, authorization, or consumer-side semantic execution.

The verifier intentionally performs no network lookup. The approved manifest is supplied by the consuming product's own release/deployment policy, keeping organizational trust and runtime authority outside this contract-only repository.

## Consequences

- Buyers can turn an archived release manifest into an executable deployment gate instead of manually comparing version strings and profile hashes.
- A package/version/profile mismatch is machine-readable and actionable without exposing another product's database or requiring a CWL control-plane service.
- The command can be used by `enterprise-architecture-core` and other consumers after an immutable Context Graph Contracts release exists, while those products continue to own their own readiness and authorization policy.
- The verifier cannot bless a new manifest. A changed package still requires the consuming product's ordinary review/provenance approval path.
- SHA-256 remains byte-identity evidence as defined in ADR 0008, not a signature or authorization claim.

## Verification

`tests/test_conformance_manifest_verifier.py` exercises exact-match acceptance, version drift, exact profile-digest drift, missing/unexpected profiles, malformed and duplicate evidence, non-object input, deterministic machine-readable CLI output, and exit-code semantics. The ordinary Python 3.11–3.14 exact-coverage and package-smoke gates must execute this surface from the reviewed head.

## References

National Institute of Standards and Technology. (2015). *Secure Hash Standard (SHS)* (FIPS PUB 180-4). U.S. Department of Commerce. https://doi.org/10.6028/NIST.FIPS.180-4
