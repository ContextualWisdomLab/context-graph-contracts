# Context Graph Contracts

**Shared, versioned interoperability contracts for the ContextualWisdomLab context and architecture ecosystem.**

Context Graph Contracts gives independently owned products a neutral place to agree on exchanged context and architecture shapes without copying one product's internal model into another repository.

## What this repository owns

This repository owns the **interoperability-contract boundary** for context and architecture exchange across ContextualWisdomLab products.

It is a contracts repository, not a product runtime. A consuming service should depend only on contracts that are explicitly published here rather than reaching into another product's internal database, implementation classes, or unpublished branch state.

## Why it matters

A shared contract boundary lets products evolve independently while keeping integration expectations reviewable. It is intended to make these distinctions explicit:

- a contract describes what may cross a product boundary;
- the producing and consuming products remain authoritative for their own behavior;
- implementation detail is not promoted into a shared API by accident;
- versioning and publication status matter before a consumer treats a contract as stable.

## Current status

This repository is currently a **minimal protected baseline**. It does not yet contain a published schema package, executable runtime, CLI, generated client, release, or compatibility guarantee.

That is the current product truth, not a missing README detail. Consumers should not invent a contract from the repository name or from draft work elsewhere in the ecosystem.

## Getting started

There is nothing to install yet because the current repository contains no executable or published contract artifact.

For an integration that may eventually use Context Graph Contracts:

1. keep the producer and consumer independently deployable;
2. do not copy internal product data models into this repository as a shortcut;
3. wait for an explicit versioned contract to be published here before making it a production dependency;
4. document the producer, consumer, compatibility expectations, and migration path together with any future contract.

## Integration boundary

```text
Producing product
      │
      │ explicit published contract
      ▼
┌───────────────────────────┐
│  Context Graph Contracts  │
│                           │
│ shared interoperability   │
│ shapes and versions       │
└─────────────┬─────────────┘
              │
              │ explicit published contract
              ▼
       Consuming product
```

The repository should remain small and provider-neutral: shared contracts belong here; domain behavior, orchestration, persistence, UI, and product-specific policy remain with their owning products.

## Quality and governance

Today the repository contains documentation only, so it does not claim runtime test coverage, benchmarks, releases, deployment readiness, certifications, or production adoption.

When contract artifacts are introduced, their README-facing status should be backed by explicit versions, validation tests, compatibility rules, changelog/release evidence, and clear migration semantics.

## Contributing

Keep additions focused on true cross-product interoperability. Before adding a shared shape, verify that more than one product actually needs the boundary and that the contract does not leak one implementation's private storage or class model into the ecosystem.

Changes that alter a published contract should carry the versioning, compatibility, validation, and migration evidence required for consumers to adopt them safely.

## License

Context Graph Contracts is licensed under the [Apache License 2.0](LICENSE).
