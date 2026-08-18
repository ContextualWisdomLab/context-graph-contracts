# Test Strategy

- Unit tests exercise every validation branch in the Python reference package.
- Structured-event tests cover tenant mismatches, type confusion, non-finite
  numbers, non-string JSON keys, Python-only values, cycles, and excessive
  nesting.
- JSON Schema tests validate all schemas against Draft 2020-12.
- Positive and negative fixtures are packaged as executable conformance
  evidence.
- Timestamp tests deliberately run Draft 2020-12 without a format checker to
  prove that default `format` annotation cannot establish semantic validity,
  then execute the packaged provider-neutral CWL Timestamp Profile v1 vectors
  through the reference parser. Calendar-impossible dates, invalid clock
  values, invalid offsets, and leap-second lexical `:60` must fail this named
  profile even though RFC 3339 itself can represent leap seconds.
- Assertion tests use consumer-shaped cases: a LineageWeave inferred
  `derived_from` edge, an enterprise-architecture `proposed` `realized_by`
  edge, cross-classified analysis-run plus employment-group membership, and
  exclusive-end temporal reconstruction.
- Conformance evidence tests execute every packaged semantic profile through
  `cwl-context-conformance`, bind the exact installed distribution version and
  profile bytes with `cwl-context-conformance-manifest`, compare that evidence
  with an independently supplied approved manifest through
  `cwl-context-conformance-verify`, and require the composite
  `cwl-context-conformance-admit` gate to rerun semantics plus exact manifest
  verification before reporting admission.
- Complete-resource evidence tests require `cwl-context-bundle-manifest` and
  `build_packaged_contract_bundle_manifest()` to bind the installed
  distribution version to SHA-256 of every explicitly published AsyncAPI,
  JSON Schema, fixture, and semantic-profile byte sequence in stable
  category-prefixed resource-path order. The regression independently reads
  those packaged bytes rather than trusting the manifest under test.
- Complete-bundle verification tests compare independently approved full
  resource evidence through `cwl-context-bundle-verify` and
  `verify_packaged_contract_bundle_manifest()`. They require exact package
  identity, strict integer count semantics, unique resource paths, and exact
  missing/unexpected/digest-different resource mismatch identities.
- Verifier regressions fail closed on package-version drift, missing,
  unexpected, duplicate, malformed, or digest-different profile/resource
  evidence, type-confused counts, unreadable or invalid UTF-8/JSON input, and
  non-object manifests. Exact matches, drift, and invalid input have distinct
  machine-readable exit semantics.
- Composite-admission regressions prove semantic failure blocks admission even
  when the approved manifest matches, manifest drift blocks admission after a
  semantic pass, and hostile manifest input reuses the same bounded strict JSON
  parser rather than a second permissive path.
- The CI matrix covers Python 3.11-3.14 and verifies the committed lockfile.
- Statement and branch coverage must both remain 100%.
- Package smoke tests install the built wheel outside the source tree, verify
  schemas, fixtures, contracts, and semantic conformance profiles are present,
  then execute the installed conformance runner, semantic manifest generator,
  approved-manifest verifier, composite admission gate, admission receipt,
  complete contract-bundle manifest, and approved full-bundle verifier from an
  isolated wheel installation.

Future language SDKs must consume the same fixture and conformance-profile
corpus and produce byte-wise compatible structured events after canonical
serialization. A language SDK is not considered compatible merely because its
package name or version matches; it must preserve the same semantic vectors and
release-evidence comparison boundary.
