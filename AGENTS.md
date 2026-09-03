# Agent Development Rules

## Authority boundary

- This repository defines interchange contracts; it must not become a runtime
 catalog, graph database, or enterprise-architecture system of record.
- Typed context assertions are interchange facts. They are not rows in a shared
 graph store and they must carry at least one context membership.
- `authoritative`, `observed`, `inferred`, `proposed`, `superseded`, and
  `rejected` describe assertion origin or an owning-domain disposition; they are
  not confidence or authorization ranks.
- Parsers and adapters must retain the supplied truth status exactly. Only the
  owning product may issue a new assertion or event that records acceptance,
  supersession, or rejection; a consumer projection must not rewrite foreign
  truth status.
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
