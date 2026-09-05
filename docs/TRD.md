# Technical Requirements Document

## Runtime

The Python reference package supports Python 3.11-3.14 and has no runtime
third-party dependencies. JSON Schema resources use Draft 2020-12. CloudEvents
structured JSON follows core version 1.0.2 while retaining the wire value
`specversion: 1.0` required by the specification. Development installs are
reproduced from the committed `uv.lock`.

## Identity requirements

- Producer context uses a tenant-scoped canonical authority URI.
- Asset subjects use authority-scoped UUIDv7 canonical asset URIs.
- CloudEvents `id` values use RFC 9562 UUIDv7 and are unique with `source`.
- `dataschema` is parsed and emitted as a CloudEvents core attribute, never as
  an extension.
- `dataschema`, when present, is an absolute URI.
- Event `source` and `subject` must resolve to the same tenant; a supplied
  `tenantid` extension must agree with that tenant.
- Structured-event core string attributes are type-checked without coercion.
- Event `data` accepts only native JSON objects, arrays, strings, booleans,
  integers, finite numbers, and null; cycles and nesting beyond 64 levels are
  rejected before serialization.
- Context assertions use UUIDv7 identity, canonical asset URIs for subject and
  object, a lower-snake predicate, a six-value truth status, a bitemporal
  interval, one to sixteen unique memberships, and a non-null typed provenance
  reference for every truth disposition.
- Parsers expose `refuse_truth_promotion()` so adapters cannot raise trust.
- Membership `membership_level` is an integer 0-15; `bool` is rejected.
- Timestamp-bearing contracts use CWL Timestamp Profile v1, whose syntax is
  derived from RFC 3339 but whose semantic contract deliberately excludes leap
  seconds so all supported SDK baselines can represent the same instants.

## Timestamp semantic conformance

Draft 2020-12's default meta-schema treats `format` as an annotation. Therefore
`format: date-time` plus the schema regex is only structural and lexical
evidence; it is not sufficient to establish that a calendar date, clock time,
or UTC offset is semantically valid.

The packaged `cwl-timestamp-profile.v1.json` is the provider-neutral semantic
conformance contract. Every consumer of a timestamp-bearing contract MUST
accept each `valid_values` vector and reject each `invalid_values` vector before
claiming semantic conformance. A consumer that cannot execute an equivalent
check MUST refuse semantic conformance rather than silently relying on JSON
Schema format annotation. CWL Timestamp Profile v1 is a strict subset of RFC
3339 and intentionally rejects leap-second lexical `:60`; it therefore has a
distinct contract name rather than claiming complete RFC 3339 acceptance.

## Compatibility policy

- Schema `$id` values are immutable after release.
- Compatible additions use optional properties or new enum-neutral extension
  fields.
- Removing an enum member, narrowing a pattern, or changing field meaning
  after release requires a new schema ID and major package version.
- Consumers must reject unknown truth-status values rather than map them to a
  more trusted status.
- ADR 0007 fixes the timestamp contract name before the first release; no
  released schema or package is being narrowed by that pre-release correction.

## Security requirements

- URI parsing is exact and does not percent-decode or Unicode-normalize input.
- Time values are timezone-aware.
- Event extensions cannot shadow core CloudEvents attributes.
- The contract validates structure, not authorization or source trust.
