# Context Graph Contracts

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ContextualWisdomLab/context-graph-contracts)

**Provider-neutral contracts for exchanging context, lineage, architecture, and impact evidence across ContextualWisdomLab products.**

Context Graph Contracts gives independently owned services a shared language for identity, truth status, time, provenance, and events **without sharing a database or surrendering domain authority**.

It is for product teams and integrators who need to answer: *Are we talking about the same object, from the same authority, at the same effective time, with evidence that can be checked?*

> This README describes the current candidate stack. Protected integration history and an immutable released package remain the authority for production consumers until this stack passes current governance and is released.

## Why it exists

Cross-product integration becomes fragile when every service invents its own identifiers, timestamps, provenance fields, event envelopes, and ideas of “truth.” Context Graph Contracts makes those exchange rules explicit while keeping product behavior in the products that own it.

| Need | What this repository provides |
| --- | --- |
| Stable identity | Canonical authority and asset URIs for cross-product references |
| Truth semantics | `authoritative`, `observed`, `inferred`, `proposed`, `superseded`, and `rejected` states |
| Time semantics | Separate real-world validity and system-recording time |
| Provenance | Exact evidence references and SHA-256 byte identity without pretending a digest proves trust |
| Context assertions | Typed subject-predicate-object assertions with context membership and cross-field rules |
| Service events | CloudEvents-based envelopes with bounded interoperable JSON payloads |
| Published contracts | JSON Schema Draft 2020-12, AsyncAPI 3.1.0 components, fixtures, and semantic conformance profiles |
| Integration evidence | Installed-package conformance, bundle identity, package evidence, and release-admission checks |

## Product boundary

This repository owns **interoperability contracts and deterministic compatibility evidence**. It is not a graph database, catalog, workflow engine, message broker, authorization service, or product runtime.

```text
Producing product
      │
      │ released contract + evidence
      ▼
┌───────────────────────────┐
│  Context Graph Contracts  │
│                           │
│ identity · truth · time   │
│ provenance · events       │
└─────────────┬─────────────┘
              │
              │ released contract + evidence
              ▼
       Consuming product
```

Owning products keep their own persistence, authorization, retry policy, audit trail, and business decisions. A compatible assertion or event does not grant a consumer permission to mutate another product's store.

## Contract baseline

### Identity and authority

A producer authority uses a tenant-scoped CWL authority URI, while a canonical asset URI identifies the object being discussed. The contract keeps **who may own a fact** separate from **who happens to transport or observe it**.

### Truth status

Cross-domain assertions carry explicit truth origin/status. Consumers must not silently promote `observed`, `inferred`, or `proposed` evidence to `authoritative`.

### Bitemporal semantics

Real-world validity stays separate from system-recording time. Open intervals are represented explicitly rather than with sentinel dates.

### Provenance

Every Context Assertion carries a typed provenance reference to the evidence or activity lineage behind its current truth disposition. The reference may bind exact source evidence with a SHA-256 digest; a digest proves byte identity only, while trust, authorization, review, and provenance admission remain separate gates.

### Events

Service notifications use CloudEvents structured JSON. The current candidate also binds Context Assertion event data to the CloudEvent envelope so event identity and assertion semantics travel together rather than being conflated.

Detailed field and cross-field rules live in the published schemas, fixtures, semantic profiles, and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Quickstart

The current source package is `cwl-context-contracts` `0.1.0` (Alpha), requires Python 3.11+, and has no runtime dependencies.

```bash
uv sync --extra dev --locked
uv run cwl-context-conformance
```

The packaged semantic inventory currently covers **CWL Timestamp Profile v1**, **Context assertion semantics v1**, **Context assertion event semantics v1**, **CloudEvent semantics v1**, the **CWL JSON interoperability profile**, and **Data-management assessment semantics v1**. The assertion-event profile composes CloudEvent identity with Context Assertion data so consumers test the complete exchange boundary rather than either layer in isolation.

A successful conformance run means the installed reference package agrees with its packaged semantic vectors. It does **not** prove that an artifact is trusted, independently approved, released from protected source, or authorized for a particular runtime.

Python consumers can use the package APIs for schemas/contracts, `ContextAssertion`, and conformance evidence rather than copying contract JSON into private forks.

## Integration and release evidence

Use progressively stronger evidence according to the integration decision you are making:

| Question | CLI |
| --- | --- |
| Does this installed package execute the published semantic vectors? | `cwl-context-conformance` |
| Which exact semantic-profile bytes are installed? | `cwl-context-conformance-manifest` |
| Does installed semantic evidence match an approved manifest? | `cwl-context-conformance-admit` |
| Which exact published contract resources are installed? | `cwl-context-bundle-manifest` / `cwl-context-bundle-verify` |
| Does the installed package satisfy the combined compatibility gate? | `cwl-context-release-admit` |
| Are wheel/sdist/SBOM/checksum bytes internally coherent? | `cwl-context-package-evidence-verify` |
| Does qualifying release evidence satisfy the deterministic admission contract? | `cwl-context-release-evidence-admit` |

These commands deliberately stop short of authority they do not own. Compatibility evidence is not a signature, independent approval, protected-branch provenance, publication authorization, or runtime permission.

Consumers should pin and admit an **immutable released distribution**. Do not integrate production behavior against an open sibling PR head just because its schema looks compatible.

## Who integrates with it

Current ecosystem consumers and producers include `semantic-data-portal`, `enterprise-architecture-core`, `pg-erd-cloud`, `LineageWeave`, and `contextual-orchestrator`. They exchange contracts or evidence while retaining their own authoritative state; they do not read one another's application databases through this package.

## Quality and status

The source package is **0.1.0 / Alpha**. The repository quality contract includes Python 3.11–3.14 verification, strict repository validation, installed-package smoke checks, package/release evidence checks, reproducibility/SBOM workflows, and an exact **100% owned production statement/branch coverage** threshold.

Those engineering gates are not customer-adoption, certification, deployment, or release claims. Open PR behavior remains candidate truth until integrated and released.

For local validation:

```bash
uv sync --extra dev --locked
uv run --extra dev python -m coverage run -m pytest -q
uv run --extra dev python -m coverage report
```

## Documentation map

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — contract architecture, identity, truth, temporal, and provenance boundaries.
- [`docs/CONTEXT_MAP.md`](docs/CONTEXT_MAP.md) — DDD ownership and neighboring contexts.
- [`docs/product-technical-gap-baseline.md`](docs/product-technical-gap-baseline.md) — current product/technical gaps and evidence state.
- [`docs/adr/`](docs/adr/) — accepted architecture decisions.
- [`docs/index.md`](docs/index.md) — documentation home.
- [`docs/doctoring/REFERENCES.md`](docs/doctoring/REFERENCES.md) — standards and research basis.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — local development and contribution procedure.

## Contributing

Keep the Shared Kernel deliberately small. Add only semantics that genuinely need to cross product boundaries; keep product-specific storage, workflow, UI, authorization decisions, and domain behavior in their owning repositories.

Changes to a published contract need versioning, compatibility tests, conformance evidence, package/release evidence, and migration guidance appropriate to their impact. New dependencies must be commercially usable under the intended distribution model and retain required provenance and attribution.

## License

Context Graph Contracts is licensed under the [Apache License 2.0](LICENSE).
