# ADR 0001: Keep this repository contract-only

- **Status:** Accepted
- **Date:** 2026-08-16

## Context

ContextualWisdomLab products need a shared, versioned way to exchange
context, lineage, architecture, and impact-analysis references. Those
products already own their systems of record. If this repository also
became a catalog, graph store, enterprise-architecture application, broker,
or workflow engine, consumers would acquire a transitive runtime dependency
and the interchange layer would compete with the products it is meant to
connect.

The interoperability surface therefore has to be something consumers can
validate without importing another CWL service. JSON Schema Draft 2020-12
is the language-neutral document dialect already used by the packaged
resources. AsyncAPI 3.1.0 is the message-contract format already named by
the packaged CloudEvent components. Neither format requires this repository
to host servers, channels, operations, or a broker topology.

## Decision

This repository contains schemas, reference value objects, fixtures, and
compatibility documentation. Runtime catalogs, graph stores, workflow
engines, and user interfaces remain in their owning products.

The published interchange surface is:

- JSON Schema Draft 2020-12 resources for identity, truth status,
  bitemporal intervals, provenance references, and the CloudEvent envelope
- an AsyncAPI 3.1.0 document that republishes reusable components for the
  shared CloudEvent payload and deliberately omits servers, channels,
  operations, broker addresses, and runtime topology

Consumers may implement other SDKs. Every SDK must pass the same fixture
corpus. A parsed contract does not grant authority to mutate another
product's store.

## Consequences

Consumers remain independently deployable and cannot acquire a transitive
runtime dependency on `semantic-data-portal` or
`enterprise-architecture-core`. Connector authors validate structure here
and keep authorization, retries, and audit trails in the owning service.

The boundary is also a compatibility constraint. Removing an enum member,
narrowing a pattern, or changing field meaning requires a new schema
identifier and a major package version. Compatible additions use optional
properties or new enum-neutral extension fields.

## References

AsyncAPI Initiative. (2026, January 31). *AsyncAPI specification* (Version 3.1.0). https://www.asyncapi.com/docs/reference/specification/v3.1.0

JSON Schema. (2022, June 16). *JSON Schema: A media type for describing JSON documents* (Draft 2020-12). https://json-schema.org/draft/2020-12/json-schema-core
