# Context Graph Contracts Foundation Design

## Goal

Create a contract-only repository that lets CWL systems exchange identity,
truth origin, bitemporal validity, provenance, and events without sharing a
database.

## Design

The Python package is a dependency-free reference implementation. JSON Schema
resources are the language-neutral wire authority. Consumers may implement
other SDKs, but all SDKs must pass the same fixture corpus.

## Scope

This foundation includes canonical URI, truth status, bitemporal interval,
provenance reference, CloudEvents envelope, context assertion, multilevel
membership, fixtures, CI, doctoring, and ADRs.
It excludes graph storage, product UIs, provider adapters, and generated
TypeScript/Rust SDKs, which are separate review units.
