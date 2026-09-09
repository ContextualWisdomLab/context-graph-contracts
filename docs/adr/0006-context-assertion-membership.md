# ADR 0006: Exchange typed assertions with multilevel membership

- **Status:** Accepted
- **Date:** 2026-08-16

## Decision

The contract layer publishes a `ContextAssertion` value object and schema. An
assertion names two canonical assets, one lower-snake predicate, one truth
status, one bitemporal interval, optional provenance, and one to sixteen unique
context memberships. Observed and authoritative assertions require provenance.
Parsers expose an explicit non-promotion helper and never raise trust.

Memberships are first-class. A parent context records nesting; additional
memberships record cross-classification. This keeps interchange facts from
being read as if the subject belonged to only one group.

The AsyncAPI document adds a reusable `ContextAssertionEvent` component and
still defines no servers, channels, operations, or broker topology.

## Consequence

LineageWeave can publish an `inferred` `derived_from` edge, enterprise
architecture can publish a `proposed` `realized_by` edge, and Orgmetra can
attach an employment-group membership without any product opening another
product's database. Consumers that need a graph store implement that store
themselves.
