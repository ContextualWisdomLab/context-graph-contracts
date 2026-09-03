# ADR 0012: Verify approved complete contract-bundle evidence

- Status: Accepted
- Date: 2026-08-18

## Context

ADR 0011 makes the complete installed JSON contract-resource set observable as
`cwl-context-bundle-manifest/v1`, but observation alone is not an admission
boundary. A consuming product still needs a deterministic way to compare the
manifest approved by its own release process with the package that is actually
installed. Comparing only the semantic-profile manifest leaves AsyncAPI,
JSON Schema, and fixture drift outside that decision.

Context Graph Contracts remains a contract-only interoperability layer. It must
not decide who is authorized to approve evidence, become a signature or trust
service, or mutate an owning product merely because byte identities match.

The current final Secure Hash Standard continues to specify SHA-256; NIST has
announced a future revision of FIPS 180-4, but a future revision is not treated
as binding production evidence until published as final. RFC 8259 remains the
wire-format basis for the hardened approved-manifest JSON input boundary.

## Decision

Publish a deterministic `cwl-context-bundle-verification/v1` decision that
compares one independently approved bundle manifest with the exact resources in
the installed `cwl-context-contracts` distribution.

The verifier:

1. rebuilds the installed bundle manifest rather than trusting caller-supplied
   installed evidence;
2. requires exact manifest format, distribution name/version, and SHA-256
   algorithm identity;
3. requires `resource_count` to be a JSON integer rather than a Boolean or
   floating-point lookalike and to equal the number of unique approved resource
   records;
4. fails closed on malformed or duplicate resource evidence;
5. reports missing, unexpected, and digest-different resources by stable
   `resource_path` identity;
6. reuses the existing bounded, strict-UTF-8, duplicate-member-rejecting,
   non-standard-constant-rejecting approved-manifest input boundary; and
7. emits exit `0` only for an exact match, exit `1` for evidence drift, and exit
   `2` for unreadable or invalid approved-manifest input.

The Python API is `verify_packaged_contract_bundle_manifest()` and the installed
CLI is `cwl-context-bundle-verify`.

## Consequences

A buyer or operator can now convert complete package-resource identity into an
executable fail-closed release/admission check instead of manually comparing
manifest JSON. The decision remains deterministic and provider-neutral.

A positive result proves only that the approved manifest and installed complete
resource bundle agree. It is not a signature, provenance attestation,
independent review, trust decision, semantic-conformance result, or runtime
authorization grant. Those remain separate owning gates.

The verifier intentionally compares the resource identities emitted by ADR 0011
and does not add a registry, graph store, catalog, workflow engine, or UI.

## Verification

- `tests/test_contract_bundle_manifest_verifier.py` covers exact acceptance,
  top-level package drift, missing/unexpected/digest-different resources,
  strict count typing, malformed/duplicate resource evidence, CLI exit
  semantics, and invalid approved JSON.
- `.github/workflows/receipt-package-smoke.yml` builds and installs the wheel,
  captures its complete bundle manifest, and verifies that manifest through the
  installed `cwl-context-bundle-verify` command.
- Ordinary CI retains exact 100% owned production statement and branch coverage.

## References

Bray, T. (2017). *The JavaScript Object Notation (JSON) data interchange format*
(RFC 8259). Internet Engineering Task Force. https://doi.org/10.17487/RFC8259

National Institute of Standards and Technology. (2015). *Secure Hash Standard
(SHS)* (FIPS PUB 180-4). U.S. Department of Commerce.
https://doi.org/10.6028/NIST.FIPS.180-4

National Institute of Standards and Technology. (2023, March 7). *Decision to
revise FIPS 180-4, Secure Hash Standard (SHS)*. Computer Security Resource
Center. https://csrc.nist.gov/News/2023/decision-to-revise-fips-180-4
