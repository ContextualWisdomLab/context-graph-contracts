# Architecture

## Bounded responsibility

```text
Producer system of record
        │
        ├── domain command and transaction
        └── versioned CWL contract event
                         │
                         ▼
              Consumer projection receipt
                         │
                         ▼
               Consumer-owned read model
```

This repository defines the middle wire contract only. Producers and consumers
own their own storage, authorization, retries, and audit trails. It is a Shared
Kernel for interoperability, not a graph store, catalog, workflow runtime, EA
database, authorization service, or UI.

## Identity and authority model

The producer authority is identified by
`urn:cwl:{tenant_id}:{authority}`. In a CloudEvent, this authority URI is the
`source`; the asset affected by the event is the `subject` and uses
`urn:cwl:{tenant_id}:{authority}:{object_type}:{uuidv7}`.

The `authority` segment names the system permitted to accept commands for an
object. A read model may project another authority's object but must not reuse
that authority's asset URI for a locally inferred object. The separate source
and subject types prevent an asset instance from being misrepresented as the
producer context used for CloudEvents deduplication.

Transporting or observing another context's fact does not transfer authority.
For an `authoritative` Context Assertion event, the CloudEvent `source` must be
the canonical authority that owns `data.subject`. An `observed` event may retain
a different same-tenant observer as `source`; the observation remains observed
and cannot be promoted by the transport or consumer.

## Truth model

The six truth states are `authoritative`, `observed`, `inferred`, `proposed`,
`superseded`, and `rejected`. They are not confidence levels. They describe how
an assertion entered the ecosystem or how its lifecycle is represented.
Confidence, scoring, verification, maliciousness verdicts, and domain-specific
risk belong in owning product payloads rather than in this shared truth enum.

Consumers retain the supplied truth state. In particular, `observed`,
`inferred`, or `proposed` evidence does not become `authoritative` merely
because a consumer stores, displays, scores, or reasons over it.

## Temporal model

`valid_from`/`valid_to` represent real-world or business validity.
`recorded_at`/`superseded_at` represent the system knowledge interval. These
axes are independent: consumers can reconstruct both "what was valid" and
"what had been recorded at a given system time" without substituting one clock
for the other.

## Provenance model

Context Assertions preserve provenance separately from authority and truth.
The shared provenance reference identifies exact source evidence and may carry
its SHA-256 byte identity and source locator. A digest establishes byte identity,
not trust, authorization, certification, or ownership.

The schema and reference SDK enforce that authoritative and observed assertions require provenance. Other truth states serialize the `provenance` field as an
explicit value or `null`; a consumer must not invent missing provenance or use a
locally generated digest to claim foreign authority.

## Context Assertion model

A Context Assertion is the smallest graph fact this repository validates. It is
a subject-predicate-object statement with one of the six truth states, a
bitemporal interval, provenance semantics, and one or more context memberships.
The object is an interchange payload, not a row in a shared graph database.

```text
                    ┌─────────────────────────┐
                    │ producing authority URI │
                    └────────────┬────────────┘
                                 │ CloudEvent source
                                 ▼
                    ┌─────────────────────────┐
                    │   ContextAssertion      │
                    │ subject --predicate-->  │
                    │ object                  │
                    │ truth_status            │
                    │ bitemporal interval     │
                    │ provenance              │
                    └───┬───────────────┬─────┘
                        │               │
            membership 0│               │membership 1
                        ▼               ▼
              analysis_run /     employment_group /
              workspace_record   other named context
```

### Context Assertion structured CloudEvent

`ContextAssertionEvent` is one versioned AsyncAPI message whose outer media type
is `application/cloudevents+json`. Its payload composes the shared CloudEvent
envelope with Context Assertion data; the enclosed CloudEvent
`datacontenttype` is `application/json`.

The envelope preserves and validates the canonical CloudEvents identity fields
`specversion`, `id`, `source`, `type`, `subject`, and `time`. A Context Assertion
event additionally requires the versioned `dataschema` for the Context
Assertion schema. Admission rejects an event when its `type`, `dataschema`, or
enclosed data media type does not match the advertised contract, when required
envelope identity is absent, or when the CloudEvent `subject` differs from
`data.subject`.

The Context Assertion data retains `truth_status`, the `valid_from`/`valid_to`
and `recorded_at`/`superseded_at` bitemporal fields, memberships, and provenance.
The packaged `context-assertion-event-semantics:v1` profile contains positive
and hostile vectors for this complete boundary, including missing event
identity, missing required provenance, wrong media type, wrong event type,
wrong `dataschema`, subject mismatch, foreign-authority rejection for
authoritative truth, and foreign-observer preservation for observed truth.

Consumers should admit this event as a single contract boundary:

1. Parse the complete structured CloudEvent rather than accepting bare assertion
   data as an equivalent message.
2. Enforce the versioned event `type`, Context Assertion `dataschema`, media-type
   split, subject identity, authority rule, truth, time, and provenance
   invariants through the packaged schema/reference SDK/conformance profile.
3. Project the assertion into consumer-owned storage under consumer-owned
   identity while preserving source authority, event identity, contract/profile
   version, admission evidence, truth, bitemporal time, and provenance.
4. Use every listed membership when interpreting the fact. A single membership
   is never a complete organizational, analytical, or social classification.

## Compatibility and admission

A matching JSON shape is not release authority. Production consumers pin an
immutable released `cwl-context-contracts` distribution and verify the packaged
schema/AsyncAPI/conformance bytes through the release-admission evidence path.
Open PR heads, predecessor checks, mutable source URLs, or a self-asserted commit
SHA do not substitute for a compatible published version and its conformance,
package, SBOM/provenance, and reproducibility evidence.

A consumer may claim Context Assertion projection compatibility only for the
contract/profile version it actually admitted. A future incompatible event,
schema, or semantic-profile revision requires a versioned compatibility path;
consumers must fail closed rather than silently interpreting it as v1.

`semantic-data-portal`, `enterprise-architecture-core`, LineageWeave, Orgmetra,
and `contextual-orchestrator` remain independently deployable. They share these
wire contracts; they do not share tables, copy source implementations, or gain
command authority over another bounded context through conformance alone.
