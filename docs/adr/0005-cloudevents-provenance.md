# ADR 0005: Use CloudEvents with provenance references

- **Status:** Accepted
- **Date:** 2026-08-16

## Context

CWL products notify one another when context, lineage, architecture, or
impact facts change. Those notifications must travel over whatever transport
each deployment already operates. They must also carry enough identity and
evidence that a consumer can project the event without reading the
producer's database or treating inferred lineage as an audited fact.

CloudEvents 1.0.2 already defines a broker-neutral structured JSON envelope,
a `source + id` replay key, and a core `dataschema` attribute. W3C PROV-O
already describes generation, derivation, and evidence entities. Neither
standard, by itself, binds a CWL asset URI to an exact evidence digest or
forbids credentials and source payloads in the envelope.

## Decision

Cross-service notifications use CloudEvents 1.0.2 structured JSON. The
`source` is a canonical tenant-scoped producer authority, the `subject` is a
canonical asset URI, and `id` is UUIDv7. The optional `dataschema` field
remains a core CloudEvents attribute and must be an absolute URI. Material
assertions reference evidence through a canonical asset URI and SHA-256
digest.

The provenance reference is a CWL profile of W3C PROV-O, not a new W3C
Recommendation. `evidence_ref` identifies the evidence entity used or
derived from (`prov:wasDerivedFrom` / the entity that `prov:wasGeneratedBy`
an activity). The SHA-256 digest is a product-defined byte-identity check
on that evidence; it proves the bytes have not changed, not that the
producer is trustworthy or authorized. Envelopes must not carry
credentials, DSNs, personal data, or raw source payloads.

The reference envelope is a full immutable value object. Parsing snapshots
the entire top-level structured mapping once before interpreting fields,
and nested JSON plus extension state is detached into immutable containers.
Equality and hashing compare the complete event value with type-exact JSON
semantics: JSON `true`, integer `1`, and number `1.0` are different values,
while JSON object member insertion order is irrelevant. Consequently two
events may share the CloudEvents replay identity `source + id` yet compare
unequal when their payload or other event content conflicts; consumers can
surface that condition instead of silently accepting a changed duplicate.

## Consequences

Transport remains broker-neutral, `source + id` supports deterministic
replay deduplication, exact value comparison exposes conflicting duplicate
content, schema identity is not confused with an extension, and
authorization plus evidence retention remain the responsibility of each
domain service.

`data` accepts only finite, acyclic, bounded JSON-native values. Event
extensions cannot shadow core CloudEvents attributes. A digest mismatch is
a contract failure; it is not an invitation to fetch or rewrite another
product's store.

## References

Cloud Native Computing Foundation. (2022). *CloudEvents specification* (Version 1.0.2). https://github.com/cloudevents/spec/tree/v1.0.2

Internet Engineering Task Force. (2024). *Universally unique identifiers (UUIDs)* (RFC 9562). RFC Editor. https://www.rfc-editor.org/rfc/rfc9562

Lebo, T., Sahoo, S., & McGuinness, D. (Eds.). (2013). *PROV-O: The PROV ontology*. World Wide Web Consortium. https://www.w3.org/TR/prov-o/
