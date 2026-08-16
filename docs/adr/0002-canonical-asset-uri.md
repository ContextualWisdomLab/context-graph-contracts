# ADR 0002: Use authority-scoped UUIDv7 URNs

- **Status:** Accepted
- **Date:** 2026-08-16

## Decision

Canonical object references use
`urn:cwl:{tenant_id}:{authority}:{object_type}:{uuidv7}`. UUIDv7 provides a
standard time-ordered identifier while the authority segment preserves command
ownership.

## Consequence

Email addresses, database sequence numbers, and provider IDs are never used as
cross-product canonical identities.
