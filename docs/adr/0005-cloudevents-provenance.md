# ADR 0005: Use CloudEvents with provenance references

- **Status:** Accepted
- **Date:** 2026-08-16

## Decision

Cross-service notifications use CloudEvents 1.0.2 structured JSON. The
`source` is a canonical tenant-scoped producer authority, the `subject` is a
canonical asset URI, and `id` is UUIDv7. The optional `dataschema` field remains
a core CloudEvents attribute and must be an absolute URI. Material assertions
reference evidence through a canonical asset URI and SHA-256 digest.

The reference envelope is a full immutable value object. Parsing snapshots the
entire top-level structured mapping once before interpreting fields, and nested
JSON plus extension state is detached into immutable containers. Equality and
hashing compare the complete event value with type-exact JSON semantics: JSON
`true`, integer `1`, and number `1.0` are different values, while JSON object
member insertion order is irrelevant. Consequently two events may share the
CloudEvents replay identity `source + id` yet compare unequal when their payload
or other event content conflicts; consumers can surface that condition instead
of silently accepting a changed duplicate.

## Consequence

Transport remains broker-neutral, `source + id` supports deterministic replay
deduplication, exact value comparison exposes conflicting duplicate content,
schema identity is not confused with an extension, and authorization plus
evidence retention remain the responsibility of each domain service.
