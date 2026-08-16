# Technical Requirements Document

## Runtime

The Python reference package supports Python 3.11-3.13 and has no runtime
third-party dependencies. JSON Schema resources use Draft 2020-12. CloudEvents
structured JSON follows core version 1.0.2 while retaining the wire value
`specversion: 1.0` required by the specification.

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
