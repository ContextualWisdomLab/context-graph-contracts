# Context Graph Contracts

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ContextualWisdomLab/context-graph-contracts)

**Versioned interoperability contracts for identity, truth, time, provenance, and Context Fabric events — without a shared database or transferred domain authority.**

Context Graph Contracts gives independently owned ContextualWisdomLab products a small, provider-neutral language for exchanging context and architecture facts. Producers can say **what object they mean, who is authoritative for it, where an assertion came from, when it was valid and recorded, and which exact evidence supports it**. Consumers can validate those claims without importing the producer's application model or writing directly to its store.

## Why use it

| Integration need | Contract responsibility |
| --- | --- |
| Stable cross-product identity | Canonical authority and asset URIs |
| Evidence origin | Explicit truth status: authoritative, observed, inferred, proposed, superseded, or rejected |
| Time-aware facts | Separate real-world validity from system-recording time |
| Provenance | Exact source/evidence references with SHA-256 byte identity where applicable |
| Context relationships | Typed Context Assertions with bounded membership and semantic invariants |
| Service notifications | CloudEvents 1.0.2 structured JSON with shared identity and interoperability rules |
| Compatibility evidence | Packaged semantic vectors, manifests, admission decisions, and release-evidence verification |

The goal is interoperability, not centralization. A shared contract lets two products understand one another while each product keeps its own authorization, persistence, workflow, retry, and audit authority.

## Current status

Context Graph Contracts is an **alpha contract stack under active development**. The candidate package metadata is currently `cwl-context-contracts` `0.1.0` for Python 3.11 or newer, with no third-party runtime dependencies.

There is **no GitHub release published for this repository yet**. An open branch, pull request, source-tree version, successful conformance run, or package build is not a released integration contract. Production consumers should bind only to an immutable released artifact after the owning release process publishes one with the required package, provenance, conformance, and approval evidence.

Until that happens, the source checkout and open contract stack are suitable for review, compatibility development, and pre-release integration testing — not for claiming a stable production dependency.

## Product boundary

Context Graph Contracts owns the **provider-neutral interoperability bounded context**: shared wire identity, authority identity, truth origin/status, bitemporal semantics, provenance, Context Assertion and CloudEvent grammar, semantic conformance vectors, and deterministic compatibility evidence.

It is **not**:

- a graph database or search engine;
- a semantic catalog or data-management system of record;
- an enterprise-architecture decision application;
- a message broker or event bus;
- a workflow/orchestration engine;
- an authorization service; or
- a shared persistence layer for ContextualWisdomLab products.

A positive contract or conformance result never grants permission to mutate another product. The producing and consuming products retain their own authorization and business authority.

## Contract baseline

### Identity and authority

A producer authority uses the URI form:

```text
urn:cwl:{tenant_id}:{authority}
```

A canonical asset uses:

```text
urn:cwl:{tenant_id}:{authority}:{object_type}:{uuidv7}
```

In the shared CloudEvent profile, `source` identifies producer authority and `subject` identifies the object being discussed. Shared identity does not make the contract repository authoritative for the underlying object.

### Truth status

Cross-domain assertions distinguish `authoritative`, `observed`, `inferred`, `proposed`, `superseded`, and `rejected`. These values describe the assertion's origin/governance state, not a generic confidence score. Consumers must not silently promote observed, inferred, or proposed data into authoritative truth.

### Bitemporal semantics

Real-world validity (`valid_from` / `valid_to`) remains distinct from system-recording time (`recorded_at` / `superseded_at`). Open intervals use `null`; sentinel dates are not part of the wire contract.

### Provenance

Material assertions can bind a source asset and digest of exact evidence bytes. A digest proves byte identity only. It does not prove trust, authorization, scientific validity, legal ownership, or business truth.

### Context Assertions and service events

Context Assertions carry typed subject–predicate–object facts with truth status, temporal validity, provenance, and context memberships. Service notifications use CloudEvents 1.0.2 structured JSON. JSON Schema Draft 2020-12 supplies structural contracts; packaged semantic vectors cover important cross-field invariants that schema validation alone cannot safely establish.

Packaged semantic conformance includes **CWL Timestamp Profile v1**, the **Context assertion** semantic profile, and the **CWL JSON interoperability profile**, alongside the shared CloudEvent profile.

The AsyncAPI 3.1.0 resource is intentionally reusable contract material. It does not declare servers, channels, operations, broker addresses, or runtime topology.

## Evaluate the source contract

The repository pins `uv` and its development environment. From a source checkout, run the same core path used by CI:

```bash
uv lock --check
uv sync --frozen --extra dev --python 3.14
uv run --frozen --extra dev --python 3.14 python -m pytest -q
uv run --frozen --extra dev --python 3.14 cwl-context-conformance
```

A successful conformance command means the installed reference package agrees with its packaged semantic vectors. It does **not** prove that another implementation is conformant, that an artifact is authentic, or that an integration is authorized.

## Integration path

A production consumer should keep the admission sequence explicit:

1. select an immutable contract release approved for that consumer;
2. run the packaged semantic conformance suite;
3. compare the exact approved semantic-profile and complete contract-bundle identities with the installed package;
4. verify package provenance and release evidence independently; and
5. apply the consumer's own authorization and domain rules before enabling the integration.

Never production-bind a mutable branch or infer approval from a passing parser test.

### Evidence CLI

The reference package exposes focused commands for consumers that need machine-checkable evidence:

| Command | Purpose |
| --- | --- |
| `cwl-context-conformance` | Execute packaged semantic vectors |
| `cwl-context-conformance-manifest` | Identify exact semantic-profile bytes |
| `cwl-context-conformance-verify` | Compare an approved profile manifest with the installed package |
| `cwl-context-conformance-admit` | Combine semantic execution with approved-profile identity |
| `cwl-context-conformance-receipt` | Produce deterministic admission evidence |
| `cwl-context-bundle-manifest` | Identify the complete published contract-resource set |
| `cwl-context-bundle-verify` | Compare an approved bundle with installed resources |
| `cwl-context-release-admit` | Combine semantic and bundle compatibility evidence |
| `cwl-context-package-evidence-verify` | Check local package-evidence integrity before provenance verification |
| `cwl-context-release-evidence-admit` | Compose the release-evidence admission boundary |

These commands deliberately stop short of trust and authorization. Their outputs are deterministic compatibility/evidence artifacts, not signatures, source provenance, reviewer approval, deployment authorization, or domain authority.

## Architecture at a glance

```text
Owning producer
  authoritative store / policy
           |
           | versioned assertion or event
           v
+--------------------------------------+
|       Context Graph Contracts        |
| identity · truth · time · provenance |
| schemas · events · conformance       |
+------------------+-------------------+
                   |
                   | validated contract data
                   v
          consumer-owned ACL
                   |
                   v
Owning consumer
  store / policy / workflow / UI
```

Products such as `semantic-data-portal`, `enterprise-architecture-core`, `pg-erd-cloud`, `LineageWeave`, and `contextual-orchestrator` may use this grammar at their integration boundaries. They remain authoritative for their own domains and must not use these contracts as an excuse for cross-service SQL or shared application tables.

## Documentation map

Start with the smallest document that answers the integration question:

- [`docs/index.md`](docs/index.md) — documentation landing and integration path.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — identity, truth, temporal, provenance, and contract architecture.
- [`docs/CONTEXT_MAP.md`](docs/CONTEXT_MAP.md) — bounded contexts and dependency direction.
- [`docs/UBIQUITOUS_LANGUAGE.md`](docs/UBIQUITOUS_LANGUAGE.md) — canonical domain vocabulary.
- [`docs/adr/`](docs/adr/) — accepted architecture decisions.
- [`docs/product-technical-gap-baseline.md`](docs/product-technical-gap-baseline.md) — current maturity, gaps, and evidence limits.
- [`docs/doctoring/REFERENCES.md`](docs/doctoring/REFERENCES.md) — standards and bibliographic sources.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — local development and contribution procedure.

## Contributing

Keep the Shared Kernel deliberately small. New contracts should represent genuinely shared interoperability semantics, not move a producer's business model, storage, workflow, or authorization decisions into this repository.

Changes should update the versioned schema/event/profile, executable conformance evidence, documentation, and compatibility boundary together. Do not treat an open ContextualWisdomLab branch as a released dependency, and do not introduce commercially incompatible inbound software or assets.

## License

Context Graph Contracts is licensed under the [Apache License 2.0](LICENSE). Third-party development and build tooling retains its own license terms and is not relicensed by this repository.
