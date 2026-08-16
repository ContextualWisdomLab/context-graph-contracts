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
  values, and payload nesting deeper than 64 levels.
- JSON Schema Draft 2020-12 resources and positive/negative conformance
  fixtures.
- Repository architecture, security, testing, doctoring, and ADR baseline.
- Typed context-assertion contract with subject-predicate-object identity,
  non-promotable truth status, bitemporal validity, optional provenance, and
  multilevel context memberships.
- Wire mappings for bitemporal intervals and provenance references.
- Shared RFC 3339 parse/format helpers used by events and intervals.
- Committed `uv.lock` and lock-checked CI so consumer installs are reproducible.
- APA 7th doctoring for RFC 3339, TSQL2/bitemporal semantics, PROV-DM, RDF 1.1,
  and multilevel-membership research.
