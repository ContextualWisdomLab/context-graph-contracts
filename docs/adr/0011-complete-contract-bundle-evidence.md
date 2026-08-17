# ADR 0011: Complete contract-bundle byte identity

- Status: Accepted
- Date: 2026-08-18

## Context

The existing conformance evidence manifest binds the installed distribution
version to the exact bytes of the four semantic conformance profiles. That is
necessary for semantic replay, but it does not identify the complete published
JSON contract surface. A consuming product could retain approved semantic
profile evidence while an AsyncAPI component document, JSON Schema, or
positive/negative fixture changed independently.

Context Graph Contracts is a contract-only interoperability layer. It must make
release evidence precise without becoming a trust registry, signature service,
authorization service, catalog, runtime graph, or workflow engine.

FIPS PUB 180-4 specifies SHA-256 as a cryptographic hash algorithm suitable for
representing exact byte identity. A hash identifies bytes; it does not establish
who authored or approved those bytes and does not prove semantic conformance or
runtime authorization.

## Decision

Publish `cwl-context-bundle-manifest/v1` as deterministic evidence for the
complete explicitly published JSON contract-resource set in the installed
`cwl-context-contracts` distribution.

The manifest:

1. binds the installed distribution name and version;
2. enumerates resources only through the repository's existing public
   `available_*_names()` surfaces rather than filesystem globbing;
3. includes every published AsyncAPI document, JSON Schema, conformance fixture,
   and semantic conformance profile;
4. hashes the exact packaged bytes of each resource with SHA-256;
5. identifies each item by a stable category-prefixed `resource_path` and emits
   resources in ascending `resource_path` order; and
6. tells operators to retain the manifest with approved release evidence and
   separately verify semantic conformance, package provenance, and runtime
   authorization before enabling an integration.

The Python API is `build_packaged_contract_bundle_manifest()` and the installed
CLI is `cwl-context-bundle-manifest`.

## Consequences

A buyer or operator can now prove which complete packaged contract-resource set
was present at a release/admission boundary and can localize byte drift to one
stable resource path. Any resource-byte change changes its SHA-256 identity.

The manifest is intentionally not signed and does not create approval, trust,
provenance, or mutation authority. Those remain separate owning gates. Semantic
compatibility still requires executable conformance rather than digest equality
alone.

Adding or removing an explicitly published resource changes `resource_count`
and the resource list and therefore requires compatibility/release review.
Installed-wheel smoke executes the CLI from the built wheel so source-tree-only
success cannot stand in for package evidence.

## Verification

- `tests/test_contract_bundle_manifest.py` checks exact packaged bytes,
  distribution-version binding, stable ordering, deterministic JSON, and the
  operator next action.
- `.github/workflows/receipt-package-smoke.yml` builds and installs the wheel,
  executes `cwl-context-bundle-manifest`, and checks the installed artifact's
  manifest shape, resource count, ordering, and digest lengths.
- CI retains exact 100% owned production statement and branch coverage.

## References

National Institute of Standards and Technology. (2015). *Secure Hash Standard
(SHS)* (FIPS PUB 180-4). U.S. Department of Commerce.
https://doi.org/10.6028/NIST.FIPS.180-4
