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
