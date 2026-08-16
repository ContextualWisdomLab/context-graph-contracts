# ADR 0002: Use tenant-scoped authority and UUIDv7 asset URNs

- **Status:** Accepted
- **Date:** 2026-08-16

## Decision

Producer authorities use `urn:cwl:{tenant_id}:{authority}`. Canonical object
references use
`urn:cwl:{tenant_id}:{authority}:{object_type}:{uuidv7}`. UUIDv7 provides a
standard time-ordered identifier while the authority segment preserves command
ownership.

Tenant, authority, and object-type segments use one bounded canonical
lower-snake spelling: 2-63 characters, a lower-case alphanumeric first word of
at least two characters, and any later words separated by exactly one
underscore. Consecutive underscores, leading/trailing underscores, and a
one-character first word followed immediately by an underscore are rejected by
both the reference implementation and packaged JSON Schemas. This prevents
consumers from inventing incompatible normalization rules for the same logical
identifier.

CloudEvents use the authority URI as `source` and the affected asset URI as
`subject`. Event IDs also use UUIDv7, so the specification's `source + id`
deduplication key is stable without treating a particular asset as the event
producer.

## Consequence

Email addresses, database sequence numbers, provider IDs, and asset identifiers
are never used as producer authority identities. Consumers can distinguish the
system that emitted an event from the object described by that event.
