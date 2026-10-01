# Context Map

## Purpose

`context-graph-contracts` is the provider-neutral interoperability contract bounded context for Context Fabric. It publishes a deliberately small Shared Kernel for exchanging identity, authority, truth origin, temporal validity, provenance and event/schema evidence between independently owned products. It does not own a runtime graph, catalog, workflow, Enterprise Architecture database, application UI or authorization decision point.

## Subdomain classification

| Subdomain | Classification | Responsibility |
| --- | --- | --- |
| Context interoperability language | Core | Canonical object references, authority references, truth status/origin, bitemporal interval semantics, provenance references and their wire invariants. |
| Contract conformance and admission | Supporting | JSON Schema and semantic profiles, conformance manifests, deterministic admission receipts and complete contract-bundle verification. |
| Package and release evidence | Generic/supporting | Reproducible package evidence, SBOM/checksum verification and protected-release attestation admission. These mechanisms protect the contract distribution; they do not create business authority. |

## Bounded-context relationships

| Context | Relationship to this repository | Ownership rule |
| --- | --- | --- |
| Enterprise Architecture Decision Plane (`enterprise-architecture-core`) | Customer / conformist to the published Shared Kernel, with an Anti-Corruption Layer where EA-specific domain concepts differ. | EA owns capabilities, applications, interfaces, technology inventory, relations, portfolio decisions, scenarios and transformations. This repository owns only the cross-product contract vocabulary. |
| Data/AI Context (`semantic-data-portal`) | Customer / conformist for portable references, provenance and event exchange. | The portal owns catalog assets, glossary, lineage, domains, data products, output ports, contracts and trust/certification. No catalog state is persisted here. |
| Physical Schema Evidence (`pg-erd-cloud`) | Upstream evidence producer through published references/events. | Physical database/schema design evidence stays owned by `pg-erd-cloud`; this repository only defines portable reference shapes. |
| Inferred Lineage (`LineageWeave`) | Upstream evidence producer through published truth/provenance semantics. | Inferred/proposed lineage remains non-authoritative unless an owning product explicitly accepts it. |
| Orchestration (`contextual-orchestrator`) | Proposal-producing customer. | Orchestration may consume contracts and propose changes but never mutates another product's authoritative store through this library. |
| Naruon and other clients | Customer / conformist. | Consumer-specific UX, search, workflow and persistence remain outside this bounded context. |

## Minimal Shared Kernel

The Shared Kernel is limited to concepts that must mean the same thing at product boundaries:

- canonical UUIDv7-based object references and authority references;
- explicit truth status/origin rather than implicit promotion of inferred or proposed facts;
- valid/effective time separated from system-recording time;
- provenance references and Context Assertion semantics;
- CloudEvents-compatible envelopes, strict timestamp profiles, JSON Schema resources and AsyncAPI-facing interoperability contracts;
- deterministic conformance/admission evidence needed to prove that a distributed contract bundle is the one a consumer evaluated.

Adding a product-specific aggregate, repository, workflow command, persistence table, UI model or provider SDK dependency to this Shared Kernel requires an ADR proving that the concept is genuinely cross-context and cannot remain behind an Anti-Corruption Layer.

## Dependency direction

Domain contract code may depend on language/runtime standards and narrowly scoped validation libraries. It must not import implementation packages from EA, Data/AI Context, physical-schema, lineage, orchestration or presentation products. Consumers depend on this published contract surface, not the reverse. Direct cross-service application-table SQL is outside the contract and prohibited.

## Current integration governance

The program's intended integration/default branch is `main`. Repository settings currently require central governance reconciliation before the active stack can be migrated safely. Until `main` is protected with the effective required checks/reviews and the stack is rebuilt against that live base, active PRs are development evidence rather than shipped product truth. See `docs/product-technical-gap-baseline.md` and the central governance owner path for the current state.
