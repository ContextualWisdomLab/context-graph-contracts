# ADR 0002: Use tenant-scoped authority and UUIDv7 asset URNs

- **Status:** Accepted
- **Date:** 2026-08-16

## Context

Cross-product interchange needs identifiers that remain stable when a
consumer projects another authority's object into its own store. Email
addresses, database sequence numbers, and provider IDs are convenient
inside one system and unsafe as shared producer identities: they leak
operational detail, collide across tenants, and cannot express who is
allowed to accept commands for an object.

RFC 9562 defines UUIDv7 as a time-ordered, standards-track unique
identifier. CloudEvents 1.0.2 already separates the producer context
(`source`) from the object the event is about (`subject`) and uses
`source + id` as the replay identity. The CWL URI grammar has to make that
separation explicit so an asset instance is never treated as the event
producer.

## Decision

Producer authorities use `urn:cwl:{tenant_id}:{authority}`. Canonical object
references use
`urn:cwl:{tenant_id}:{authority}:{object_type}:{uuidv7}`. UUIDv7 provides a
standard time-ordered identifier while the authority segment preserves
command ownership.

Tenant, authority, and object-type segments use one bounded canonical
lower-snake spelling: 2-63 characters, a lower-case alphanumeric first word
of at least two characters, and any later words separated by exactly one
underscore. Consecutive underscores, leading/trailing underscores, and a
one-character first word followed immediately by an underscore are rejected
by both the reference implementation and packaged JSON Schemas. This
prevents consumers from inventing incompatible normalization rules for the
same logical identifier.

CloudEvents use the authority URI as `source` and the affected asset URI as
`subject`. Event IDs also use UUIDv7, so the specification's `source + id`
deduplication key is stable without treating a particular asset as the
event producer. URI parsing is exact: it does not percent-decode or
Unicode-normalize input.

## Consequences

Email addresses, database sequence numbers, provider IDs, and asset
identifiers are never used as producer authority identities. Consumers can
distinguish the system that emitted an event from the object described by
that event.

A read model may project another authority's object but must not reuse that
authority's asset URI for a locally inferred object. Event `source` and
`subject` must resolve to the same tenant; a supplied `tenantid` extension
must agree with that tenant.

## References

Cloud Native Computing Foundation. (2022). *CloudEvents specification* (Version 1.0.2). https://github.com/cloudevents/spec/tree/v1.0.2

Internet Engineering Task Force. (2024). *Universally unique identifiers (UUIDs)* (RFC 9562). RFC Editor. https://www.rfc-editor.org/rfc/rfc9562
