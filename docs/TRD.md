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
  interval, one to sixteen unique memberships, and provenance whenever the
  status is `observed` or `authoritative`.
- Parsers expose `refuse_truth_promotion()` so adapters cannot raise trust.
- Membership `membership_level` is an integer 0-15; `bool` is rejected.
- RFC 3339 timestamps are parsed and serialized by the shared helpers used by
  events and intervals.

## Compatibility policy

- Schema `$id` values are immutable.
- Compatible additions use optional properties or new enum-neutral extension
  fields.
- Removing an enum member, narrowing a pattern, or changing field meaning
  requires a new schema ID and major package version.
- Consumers must reject unknown truth-status values rather than map them to a
  more trusted status.

## Security requirements

- URI parsing is exact and does not percent-decode or Unicode-normalize input.
- Time values are timezone-aware.
- Event extensions cannot shadow core CloudEvents attributes.
- The contract validates structure, not authorization or source trust.
