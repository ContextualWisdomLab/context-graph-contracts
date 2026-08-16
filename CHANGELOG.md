# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added

- Canonical tenant-scoped producer authority URI contract.
- Canonical UUIDv7-backed CWL asset URI contract.
- Truth-status vocabulary separating authoritative, observed, inferred, and
  proposed assertions.
- Bitemporal interval and provenance-reference contracts.
- CloudEvents 1.0.2 structured-event reference implementation with UUIDv7
  event identity, producer-authority `source`, asset `subject`, and optional
  core `dataschema` support.
- Tenant-consistency validation between CloudEvents producer `source`, asset
  `subject`, and an optional `tenantid` extension.
- Fail-closed structured-event validation for non-string core attributes,
  non-finite numbers, non-string JSON keys, cyclic containers, non-JSON Python
  values, payload nesting deeper than 64 levels, and integers outside the RFC
  8259 exact interoperable range `[-(2**53)+1, (2**53)-1]`.
- JSON Schema Draft 2020-12 resources and positive/negative conformance
  fixtures.
- Provider-neutral semantic conformance profiles for the CWL Timestamp Profile,
  Context Assertion cross-field invariants, and exact JSON integer exchange;
  installed-package smoke tests execute the same vectors consumers receive.
- Repository architecture, security, testing, doctoring, and ADR baseline.
- Typed context-assertion contract with subject-predicate-object identity,
  non-promotable truth status, bitemporal validity, optional provenance, and
  multilevel context memberships.
- Wire mappings for bitemporal intervals and provenance references.
- CWL Timestamp Profile v1 parse/format helpers, with pre-release RFC3339-named
  aliases retained for compatibility; serialization rejects timezone offsets
  that cannot be represented by the profile.
- Committed `uv.lock` and lock-checked CI so consumer installs are reproducible.
- Exact-head SPDX JSON SBOM and SHA-256 package evidence on pull requests and
  protected-main builds, plus protected-main SLSA build-provenance and SBOM
  attestations using immutably pinned GitHub/Anchore actions.
- APA 7th doctoring for RFC 3339, RFC 8259, TSQL2/bitemporal semantics, PROV-DM,
  RDF 1.1, and multilevel-membership research.
