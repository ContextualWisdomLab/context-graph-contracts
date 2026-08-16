# Product Requirements Document

## Product definition

Context Graph Contracts is the provider-neutral interoperability layer for the
CWL Context Fabric. It allows independently deployed products to exchange
stable object references, temporal facts, provenance references, and service
events without sharing databases or confusing inferred relationships with
approved facts.

## Primary users

- CWL service maintainers publishing context or architecture events.
- Connector authors integrating `semantic-data-portal`,
  `enterprise-architecture-core`, `pg-erd-cloud`, and LineageWeave.
- Security and governance reviewers validating authority and provenance.

## P0 requirements

1. Canonical asset identifiers must identify tenant, authority, object type,
   and UUIDv7 object identity.
2. Truth status must preserve the difference between authoritative, observed,
   inferred, proposed, superseded, and rejected assertions.
3. Valid time must remain distinct from system-recording time.
4. Events must use CloudEvents structured JSON and carry only opaque references
   in cross-service metadata.
5. Provenance must bind an evidence reference to an exact SHA-256 digest.
6. Contracts must be usable without importing a CWL runtime service.
7. Schemas, code, and fixtures must be versioned and backward-compatible.

## Excluded from P0

- Graph persistence or query execution.
- Catalog, EA, workflow, or UI functionality.
- Automatic promotion of inferred relationships.
- Provider-specific Atlan or SAP LeanIX payloads.
