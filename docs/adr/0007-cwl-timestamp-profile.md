# ADR 0007: Name the portable timestamp contract explicitly

- **Status:** Accepted
- **Date:** 2026-08-17

## Context

The unreleased foundation described timestamp fields as RFC 3339 while its
Python reference parser used `datetime.fromisoformat()`. That implementation
correctly rejected impossible calendar dates and clock values, but it also
rejected leap-second lexical `:60`, which RFC 3339 permits at valid insertion
points. Separately, Draft 2020-12's default meta-schema treats `format` as an
annotation, so `format: date-time` cannot by itself guarantee semantic calendar
or clock validity for language-neutral consumers.

Calling the narrower behavior simply "RFC 3339" therefore made the schema,
reference parser, and portability claim disagree.

## Decision

Before the first package or schema release, define **CWL Timestamp Profile v1**
as the timestamp contract for Context Fabric events and bitemporal intervals.
Its lexical basis is RFC 3339, but the profile deliberately excludes leap-second
`:60` values so all supported SDK baselines can represent and compare the same
instants without lossy normalization.

The JSON Schema regex and `format: date-time` remain structural and lexical
guards. Semantic conformance is a separate mandatory gate defined by the
packaged `cwl-timestamp-profile.v1.json` positive and negative vectors. A
consumer that cannot execute an equivalent semantic check must refuse semantic
conformance.

The canonical Python API is `parse_cwl_timestamp()` /
`format_cwl_timestamp()`. The pre-release `parse_rfc3339_timestamp` and
`format_rfc3339_timestamp` names remain temporary compatibility aliases only;
they do not name the normative contract and may be removed before 1.0.

## Consequences

- Impossible calendar dates, invalid clock values, invalid offsets, and
  leap-second lexical `:60` fail the named CWL profile deterministically.
- RFC 3339 remains the syntax basis and is cited accurately; the product no
  longer claims full RFC 3339 semantic acceptance.
- Language SDKs can run the same machine-readable vectors without importing the
  Python implementation.
- No released compatibility promise is narrowed: this correction occurs before
  the first Context Fabric contract release from protected `main`.

## References

JSON Schema. (2022, June 16). *JSON Schema validation: A vocabulary for
structural validation of JSON* (Draft 2020-12), §7.2.
https://json-schema.org/draft/2020-12/json-schema-validation

Klyne, G., & Newman, C. (2002). *Date and time on the Internet: Timestamps*
(RFC 3339), §5.7. RFC Editor. https://www.rfc-editor.org/rfc/rfc3339
