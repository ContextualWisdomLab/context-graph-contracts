# ADR 0003: Represent assertion origin explicitly

- **Status:** Accepted
- **Date:** 2026-08-16

## Decision

Every cross-domain assertion uses one of six truth statuses. `authoritative`
means approved by the owning domain; `observed` means deterministically
measured; `inferred` means analytically derived; `proposed` awaits review;
`superseded` and `rejected` preserve historical decisions.

## Consequence

LineageWeave and LLM outputs cannot silently enter authoritative audit views.
