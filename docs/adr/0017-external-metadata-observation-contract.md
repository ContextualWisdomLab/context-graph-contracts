# ADR 0017: Exchange external metadata observations as non-authoritative evidence

- Status: Accepted
- Date: 2026-10-06
- Issue: ContextualWisdomLab/context-graph-contracts#26

## Context

Consumers need to bring metadata from external catalogs into Context Fabric, for example the table and column metadata an OpenMetadata deployment reports. Today there is no provider-neutral contract for that exchange. Without one, each consumer writes its own adapter. Adapters can then quietly treat a catalog's report as authoritative, mix up tenants that share external IDs, or replay the same payload as several facts.

This repository is contract-only (ADR 0001). It must not become a catalog, a metadata store, a lineage graph or a workflow, and it must not depend on any provider SDK.

## Decision

1. The package publishes four provider-neutral contracts. All of them are CWL-authored; no vendor schema, payload or field name is copied.
   - **External Metadata Source**: the canonical source authority URI, a thin `provider_code` profile value, the source release, an HTTPS schema URI with its SHA-256 pin, and a lifecycle.
   - **External Entity Reference**: an opaque `external_id`, an external entity type and a fully qualified name. Its identity is `(source_authority, external_entity_type, external_id)`. The authority URI carries the tenant, so equal external IDs in different tenants never collide. `external_id` is never normalized.
   - **Metadata Observation Envelope**: exactly one existing six-value Truth Status, a Bitemporal Interval, a required Provenance Reference, payload and normalized SHA-256 digests, a replay identity and an optional supersession reference.
   - **Metadata Projection Receipt**: the admission decision over one observation. It carries a bounded reason code and the contract, schema, profile and admission versions.
2. The source tenant comes only from `source_authority`. There is no separate tenant field that could disagree with it.
3. Truth status is retained exactly and never ranked. A foreign source may report `observed`, `inferred` or `proposed`. Only the authority that owns `subject_ref` may report `authoritative`, `superseded` or `rejected`. Any other source's owner-controlled disposition gets a rejected receipt with `owner_disposition_forbidden`. This reuses the Context Assertion owner-controlled rule (ADR 0003, ADR 0006).
4. The replay identity is SHA-256 over the UTF-8 JSON array `["cwl-external-metadata-replay/v1", source_authority, tenant_id, external_entity_type, external_id, source_release, payload_sha256]`, written with no insignificant whitespace. Every element is a string, so the encoding is RFC 8785 canonical, and the array framing keeps field boundaries unambiguous. A supplied `replay_id` that differs from the derived value gets `replay_identity_mismatch`. Changed bytes therefore cannot reuse an earlier replay identity.
5. Truth status and supersession are deliberately excluded from the replay key. Two consequences follow:
   - An owner re-emit of identical bytes shares a replay identity with the earlier observation.
   - Supersession is carried by a new `observation_id` and `supersedes_observation_id`, never by an edit. A consumer must not drop a supersession merely because its replay identity was already seen.
6. Admission is a pure function, `admit_metadata_observation`.
   - Structural, type and grammar failures raise and mint no receipt. These include duplicate JSON members, `NaN`/`Infinity`, inexact integers, input over 64 KiB, unknown fields, non-canonical identifiers and missing provenance.
   - Semantic failures return a rejected receipt with one allowlisted reason: `source_authority_mismatch`, `tenant_scope_mismatch`, `provenance_scope_mismatch`, `replay_identity_mismatch`, `supersession_self_reference`, `supersession_authority_mismatch` or `owner_disposition_forbidden`.
   - Admitted receipts carry `admitted_evidence` or `admitted_owner_disposition`.
   - A receipt can only be minted by admission, and its stored decision must equal the rule result.
   - Admission keeps no replay registry, "latest observation" lookup or other state.
7. The semantic profile `external-metadata-observation-semantics.v1.json` publishes valid, rejected, invalid, raw-JSON and replay vectors so non-Python consumers can check the same invariants. The JSON Schemas are structural only.

## Consequences

Consumers get one fail-closed way to admit external catalog observations without giving the catalog authority over subjects owned elsewhere. `provider_code = openmetadata` is profile data, not a dependency; the DDD fitness test forbids importing `openmetadata` or its `metadata` package.

This is a reference interoperability contract, **not a catalog**, metadata store, lineage graph or ingestion workflow. Persistence, deduplication policy, reconciliation and projection remain owned by consumers.

Adding new packaged resources under distribution version `0.1.0` changes the bundle and conformance inventories. Previously approved `0.1.0` conformance or bundle manifests will no longer verify against this source. Choosing the version bump belongs to the release owner, not this change.

## Not decided here (remaining work)

- A trusted registry that pins provider schema digests. This change validates only the URI and digest format.
- Normalized-hash recomputation. The envelope does not carry the normalized object, so consumers own normalization.
- `metadata_relation_observation` for table and column lineage endpoints.
- CloudEvent type and AsyncAPI message bindings for observations and receipts.
- Rust and TypeScript bindings.
- Owner transition evidence beyond the owner-authority check.
- Any release, tag or consumer-adoption claim.

## Verification

- `tests/test_external_metadata.py` covers the DTO round trip for all six statuses, the replay derivation against an independent implementation, cross-tenant and framing separation, and hostile mappings and JSON text.
- `tests/test_external_metadata_admission.py` covers every reason code, owner-controlled forgery, supersession as a new fact, replay idempotency, receipt-minting bypass and profile identity drift.
- `tests/test_external_metadata_conformance.py` covers Draft 2020-12 schema validity, positive and negative fixtures, and the packaged profile through the buyer-facing runner, including drift reporting for every vector family.
- `.github/tests/test_workflow_integration_branches.py` keeps the installed-package CI inventories equal to the shipped resources.
