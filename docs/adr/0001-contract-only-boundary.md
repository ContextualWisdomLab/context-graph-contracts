# ADR 0001: Keep this repository contract-only

- **Status:** Accepted
- **Date:** 2026-08-16

## Decision

This repository contains schemas, reference value objects, fixtures, and
compatibility documentation. Runtime catalogs, graph stores, workflow engines,
and user interfaces remain in their owning products.

## Consequence

Consumers remain independently deployable and cannot acquire a transitive
runtime dependency on `semantic-data-portal` or `enterprise-architecture-core`.
