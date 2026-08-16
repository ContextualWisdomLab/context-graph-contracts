# Context Graph Contracts

`context-graph-contracts` defines the shared, versioned interoperability
contracts used by ContextualWisdomLab context, lineage, architecture, and
impact-analysis products.

The repository is deliberately **not** a graph database, catalog, enterprise
architecture application, broker topology, or workflow engine. It owns only
contracts that let independent systems exchange references and evidence without
surrendering their domain authority.

## Contract baseline

- producer authority URI: `urn:cwl:{tenant_id}:{authority}`
- canonical asset URI:
  `urn:cwl:{tenant_id}:{authority}:{object_type}:{uuidv7}`
- truth status: `authoritative`, `observed`, `inferred`, `proposed`,
  `superseded`, or `rejected`
- bitemporal validity: real-world validity and system-recording time remain
  distinct
- provenance: every material assertion can point to a source asset and a
  SHA-256 evidence digest
- service events: CloudEvents 1.0.2 structured JSON; `source` identifies the
  producer authority, `subject` identifies the affected asset, both references
  share one tenant boundary, event IDs use UUIDv7, `dataschema` remains a core
  CloudEvents attribute, and `data` accepts only finite, acyclic, bounded
  JSON-native values
- context assertion: a typed subject-predicate-object statement with truth
  status, bitemporal validity, optional provenance, and one or more context
  memberships so consumers can exchange graph edges without sharing a store
- schema dialect: JSON Schema Draft 2020-12
- message contract: AsyncAPI 3.1.0 reusable components for the shared
  CloudEvent payload and the context-assertion payload, deliberately without
  servers, channels, operations, broker addresses, or runtime topology

The Python reference package exposes `load_schema()` for JSON Schema resources,
`load_contract()` for the packaged AsyncAPI document, `ContextAssertion` for
typed graph edges, and conformance fixtures for consumer validation. These are
interoperability artifacts; they do not grant a consumer authority to mutate
another product's store. Parse an assertion, keep its truth status, and project
it into your own store. Do not promote `observed`, `inferred`, or `proposed`
edges to `authoritative` inside an adapter.

## Repository boundary

Consumers include `semantic-data-portal`, `enterprise-architecture-core`,
`pg-erd-cloud`, `LineageWeave`, and `contextual-orchestrator`. Consumers must
not read one another's databases. They exchange contracts or events and keep
their own authoritative state.

## Development

```bash
uv sync --extra dev
uv run --extra dev python -m coverage run -m pytest -q
uv run --extra dev python -m coverage report
```

See `docs/ARCHITECTURE.md` and the ADRs for the authority and compatibility
rules.
