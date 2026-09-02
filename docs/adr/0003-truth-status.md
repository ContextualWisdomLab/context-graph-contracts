# ADR 0003: Represent assertion origin explicitly

- **Status:** Accepted
- **Date:** 2026-08-16

## Context

Context, lineage, architecture, and impact products all emit assertions
that later appear in audit and impact views. Some of those assertions are
approved by the owning domain. Others are measured, derived by analysis,
suggested for review, or later withdrawn. If interchange omitted origin,
LineageWeave projections and LLM outputs could be read as approved facts.

W3C PROV-O already describes how an entity was generated, derived, and
invalidated. It does not publish a closed six-value vocabulary for CWL
interchange. This repository therefore needs an explicit, fail-closed
status field that consumers can validate without interpreting PROV graphs.

## Decision

Every cross-domain assertion uses one of six truth statuses.
`authoritative` means approved by the owning domain; `observed` means
deterministically measured; `inferred` means analytically derived;
`proposed` awaits review; `superseded` and `rejected` preserve historical
decisions.

These values are a CWL profile of W3C PROV-O provenance, not a new W3C
Recommendation. The profile uses PROV relations as the semantic basis and
does not extend the W3C recommendation:

- `authoritative` and `observed` classify the generating activity
  (`prov:wasGeneratedBy`): command acceptance by the owning authority
  versus deterministic measurement
- `inferred` classifies derivation (`prov:wasDerivedFrom`) from other
  recorded entities
- `proposed` is generated but not yet accepted by the owning authority
- `superseded` and `rejected` record invalidation (`prov:wasInvalidatedBy`)
  while retaining the historical assertion

Truth status is not a confidence score and does not authorize a consumer.
Confidence and verification evidence belong in domain-specific payloads.
Parsers and adapters must not promote `observed`, `inferred`, or
`proposed` assertions to `authoritative`.

## Consequences

LineageWeave and LLM outputs cannot silently enter authoritative audit
views. Consumers must reject unknown truth-status values rather than map
them to a more trusted status.

Owning products remain responsible for the workflow that accepts a
`proposed` assertion or records a later `superseded` or `rejected`
decision. This repository only carries the resulting status on the wire.

## References

Lebo, T., Sahoo, S., & McGuinness, D. (Eds.). (2013). *PROV-O: The PROV ontology*. World Wide Web Consortium. https://www.w3.org/TR/prov-o/
