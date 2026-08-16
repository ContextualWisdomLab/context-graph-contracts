# Context Graph Contracts

`context-graph-contracts` defines the shared, versioned interoperability
contracts used by ContextualWisdomLab context, lineage, architecture, and
impact-analysis products.

The repository is deliberately **not** a graph database, catalog, or enterprise
architecture application. It owns only contracts that let independent systems
exchange references and evidence without surrendering their domain authority.

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
- schema dialect: JSON Schema Draft 2020-12

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
