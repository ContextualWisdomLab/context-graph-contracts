# Context Graph Contracts

Context Graph Contracts is the shared interoperability layer for ContextualWisdomLab products that exchange context, lineage, architecture, provenance, and impact-analysis facts without sharing application databases or transferring domain authority.

## Start here

Use this repository when two products need to agree on wire identity, truth status, bitemporal semantics, provenance, Context Assertions, CloudEvents, or release/conformance evidence.

The project publishes JSON Schema Draft 2020-12 resources, AsyncAPI reusable components, semantic conformance profiles and a Python reference package. It is not a graph database, catalog, workflow engine, broker, or application runtime.

## Integration path

1. Choose the released contract version approved by the consuming product.
2. Run the packaged semantic conformance suite.
3. Verify exact approved semantic-profile and full contract-bundle identities.
4. Verify package/provenance evidence independently.
5. Keep runtime authorization and source-system authority in the consuming/owning products.

## Core documentation

- [Repository overview](../README.md)
- [Architecture](ARCHITECTURE.md)
- [Context Map](CONTEXT_MAP.md)
- [Ubiquitous Language](UBIQUITOUS_LANGUAGE.md)
- [Architecture decisions](adr/)
- [Research and standards references](doctoring/REFERENCES.md)

## Current status

The contract stack is under active development and remains subject to normal protected integration, package, security, reproducibility, and review governance. Documentation and draft pull requests are not themselves release authority. Consumers should use immutable released artifacts and their associated evidence once available.
