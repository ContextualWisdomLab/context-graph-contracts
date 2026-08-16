# Agent Development Rules

## Authority boundary

- This repository defines interchange contracts; it must not become a runtime
  catalog, graph database, or enterprise-architecture system of record.
- Never promote `observed`, `inferred`, or `proposed` assertions to
  `authoritative` inside a parser or adapter.
- Contract changes are backward-compatible by default. Breaking changes require
  a new schema identifier and a major version.

## Identifiers and time

- Canonical identifiers use UUIDv7 and the exact CWL URN grammar.
- Real-world validity and system-recording time are separate fields.
- Open intervals use omitted end values; do not invent sentinel dates.

## Quality

- Production statement and branch coverage must remain 100%.
- Public modules, classes, functions, methods, and properties require
  docstrings.
- JSON schemas use Draft 2020-12 and include positive and negative fixtures.
- Database object names used in examples must contain at least two snake-case
  words.
