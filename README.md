# Context Graph Contracts

Context Graph Contracts is the shared, versioned interoperability layer for
ContextualWisdomLab products that exchange **context**, **lineage**,
**architecture**, and **impact-analysis** facts.

Independent systems use these contracts to name the same objects, say how an
assertion entered the ecosystem, and point at evidence — without sharing a
database or surrendering domain authority.

## What this is not

This repository is not a graph database, data catalog, enterprise-architecture
application, message broker, or workflow engine. It does not store entities,
run queries, host a UI, or own a runtime topology.

It publishes versioned schemas, a reference Python package, and compatibility
rules. Owning products keep their own stores, authorization, retries, and
audit trails.

## Contract baseline

Operators and integrators can rely on these interchange rules.

**Producer authority URI.**
`urn:cwl:{tenant_id}:{authority}` names the system allowed to accept commands
for an object. In a CloudEvent this value is `source`.

**Canonical asset URI.**
`urn:cwl:{tenant_id}:{authority}:{object_type}:{uuidv7}` is the stable identity
of the object being discussed. In a CloudEvent this value is `subject`.

**Truth status.**
Every cross-domain assertion carries one of `authoritative`, `observed`,
`inferred`, `proposed`, `superseded`, or `rejected`. These values describe
origin, not confidence. Consumers must not promote `observed`, `inferred`, or
`proposed` assertions to `authoritative`.

**Bitemporal validity.**
Real-world validity (`valid_from` / `valid_to`) stays distinct from
system-recording time (`recorded_at` / `superseded_at`). Open intervals omit
the end value; they do not use sentinel dates.

**Provenance.**
A material assertion can point to a source asset and a SHA-256 digest of the
exact evidence bytes. A digest proves byte identity, not trust or
authorization.

**Service events.**
Notifications use CloudEvents 1.0.2 structured JSON. `source` and `subject`
share one tenant. Event IDs are UUIDv7. `dataschema` remains a core
CloudEvents attribute. Payloads accept only finite, acyclic, bounded
JSON-native values.

The published surface is JSON Schema Draft 2020-12 plus AsyncAPI 3.1.0
reusable components for the shared CloudEvent payload. The AsyncAPI document
does not define servers, channels, operations, broker addresses, or runtime
topology.

The Python reference package exposes `load_schema()` and `load_contract()`
plus conformance fixtures. These artifacts do not grant a consumer authority
to mutate another product's store.

## Who consumes these contracts

`semantic-data-portal`, `enterprise-architecture-core`, `pg-erd-cloud`,
`LineageWeave`, and `contextual-orchestrator` exchange contracts or events and
keep their own authoritative state. They do not read one another's databases.

## Further reading

- Architecture and identity, truth, and temporal models: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Accepted decisions: [`docs/adr/`](docs/adr/)
- Bibliographic sources: [`docs/doctoring/REFERENCES.md`](docs/doctoring/REFERENCES.md)
- Local development: [`CONTRIBUTING.md`](CONTRIBUTING.md)
