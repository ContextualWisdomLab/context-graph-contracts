# ADR 0004: Separate valid time from system time

- **Status:** Accepted
- **Date:** 2026-08-16

## Context

Impact and audit consumers need two different answers from the same
assertion: when the fact held in the world, and when the producing system
knew that fact. Collapsing those clocks lets a later recording leak into an
earlier knowledge cutoff. Sentinel end dates create the opposite problem:
consumers cannot tell an open interval from an invented far-future bound.

W3C PROV-O already distinguishes generation and invalidation of an entity
from the times of the activity that produced it. That distinction is enough
to keep recorded knowledge separate from real-world validity. This
repository does not adopt a separate temporal-database calculus; it carries
both intervals on the interchange contract.

## Decision

Interchange contracts carry real-world validity and system-recording
intervals. Canonical producers omit an open interval's end value instead of
using sentinel dates or emitting JSON null.

Version-one consumers remain backward-compatible with payloads that were
previously admitted with explicit null end members. They interpret null as an
open end and normalize it to omission when serializing again. Rejecting that
already-admitted v1 spelling would require a new schema identifier and major
version under the repository compatibility rule.

- `valid_from` / `valid_to` are the real-world validity window
- `recorded_at` / `superseded_at` are the system's knowledge interval

The recorded assertion is the PROV entity. `recorded_at` is when that
entity was generated; `superseded_at` is when it was invalidated
(`prov:generatedAtTime` / `prov:invalidatedAtTime`). Real-world validity is
a separate window on the same assertion so consumers can reconstruct "what
was true" independently of "what was known." Both clocks use timezone-aware
timestamps. Exclusive ends apply: a fact is valid at `instant` when
`valid_from <= instant` and `valid_to` is omitted/null-open or
`instant < valid_to`.

## Consequences

Consumers can reproduce historical knowledge cutoffs and avoid
future-information leakage in impact or audit analysis. Canonical emitted
payloads use omission for an open `valid_to` or `superseded_at`; v1 input
compatibility for explicit null does not make null a second producer form.

This contract validates temporal structure only. Authorization, retention,
and the decision to supersede a recorded assertion remain with the owning
domain service.

## References

Lebo, T., Sahoo, S., & McGuinness, D. (Eds.). (2013). *PROV-O: The PROV ontology*. World Wide Web Consortium. https://www.w3.org/TR/prov-o/
