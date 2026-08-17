# ADR 0010: Publish deterministic conformance admission receipts

- Status: Accepted
- Date: 2026-08-17

## Context

ADR 0009 makes an independently approved conformance manifest executable as a
fail-closed installed-package gate. A consuming product still needs durable,
portable evidence identifying exactly which approved manifest and admission
result it evaluated. Persisting the entire admission payload is possible, but
it invites each consumer to invent its own hashing and serialization convention,
which makes cross-language evidence comparison unreliable.

The contract package owns the manifest and admission evidence formats, so it may
publish a deterministic evidence identity. It must not become an approval
registry, signing service, provenance authority, deployment controller, or
runtime authorization service.

RFC 8785 defines a JSON Canonicalization Scheme (JCS) for repeatable hashing and
signing inputs. RFC 8785 is Informational rather than an IETF Standards Track
RFC, so this ADR treats it as an interoperability profile for the receipt
preimage rather than claiming an IETF standard mandate. NIST FIPS 180-4 remains
the current published Secure Hash Standard defining SHA-256 while NIST prepares
a revision.

## Decision

Publish `build_packaged_conformance_admission_receipt()` and the installed
`cwl-context-conformance-receipt` command. A receipt:

1. evaluates the existing composite admission decision rather than creating a
   second verifier;
2. identifies canonicalization as `RFC8785`, manifest normalization as
   `profile_name_ascending`, and the digest algorithm as `sha256`;
3. hashes the independently supplied approved-manifest semantics after
   constraining them to the exact `cwl-context-conformance-manifest/v1` member
   set, normalizing the semantically unordered profile evidence by ascending
   `profile_name`, and then applying JCS;
4. rejects unknown top-level or profile members, non-string contract fields,
   booleans or integers outside the exact interoperable JSON integer range for
   `profile_count`, malformed profile collections, and strings containing
   unpaired Unicode surrogate code points;
5. hashes the complete admission evidence mapping separately so a changed
   semantic result cannot reuse an earlier admission-evidence identity;
6. uses exit `0` for admitted evidence, exit `1` for shape-valid evidence drift,
   and exit `2` for unreadable, invalid, or ambiguous receipt input;
7. returns the same operator next action as the underlying admission decision;
8. remains deterministic and offline, without network lookup, secret material,
   signatures, or mutable approval state.

The verifier already treats profile evidence as a name-to-digest set rather than
an order-sensitive sequence. Therefore the receipt normalizes that list before
hashing, so two verifier-equivalent manifests cannot acquire different receipt
identities merely because their JSON arrays were serialized in a different
order. After this normalization, the accepted manifest and admission mappings
contain fixed ASCII object member names, JCS-safe strings, booleans, lists, and
exact-range integers. Within that constrained value set, compact UTF-8
serialization with recursively sorted fixed member names is the RFC 8785
representation. A published exact digest vector prevents another SDK from
silently implementing a different serialization convention.

## Consequences

- A deployment or evidence store can persist two compact SHA-256 identities and
  later compare them across independent implementations.
- JSON object-member order and profile-array order do not affect the approved
  manifest identity when the verifier semantics are unchanged.
- Unknown extension members fail closed instead of receiving an undocumented
  hash meaning.
- A receipt proves deterministic evidence identity only. It does not prove who
  approved the manifest, who built the artifact, whether the artifact is signed,
  whether an actor is authorized, or whether deployment should proceed.
- Consumers still verify protected-build provenance, SBOM/package identity,
  independent review, and runtime authorization in their owning boundaries.

## Verification

`tests/test_conformance_admission_receipt.py` covers admitted and rejected
receipts, object-member and profile-array order independence, an exact published
canonical digest vector, digest drift, ambiguous-member rejection,
machine-readable CLI behavior, and exit codes.
`tests/test_conformance_admission_receipt_jcs.py` rejects integers outside the
exact JSON interoperability range and unpaired Unicode surrogates. The
`receipt-package-smoke` workflow builds a wheel, installs it in an isolated
environment, executes the installed manifest and receipt commands, and verifies
the declared RFC 8785 / `profile_name_ascending` / SHA-256 receipt profile.

## References

National Institute of Standards and Technology. (2015). *Secure Hash Standard
(SHS)* (FIPS PUB 180-4). U.S. Department of Commerce.
https://doi.org/10.6028/NIST.FIPS.180-4

Rundgren, A., Jordan, B., & Erdtman, S. (2020). *JSON Canonicalization Scheme
(JCS)* (RFC 8785). RFC Editor. https://www.rfc-editor.org/rfc/rfc8785
