# ADR 0005: Use CloudEvents with provenance references

- **Status:** Accepted
- **Date:** 2026-08-16

## Decision

Cross-service notifications use CloudEvents 1.0.2 structured JSON. The
`source` is a canonical tenant-scoped producer authority, the `subject` is a
canonical asset URI, and `id` is UUIDv7. The optional `dataschema` field remains
a core CloudEvents attribute and must be an absolute URI. Material assertions
reference evidence through a canonical asset URI and SHA-256 digest.

## Consequence

Transport remains broker-neutral, `source + id` supports deterministic replay
deduplication, schema identity is not confused with an extension, and
authorization plus evidence retention remain the responsibility of each domain
service.
