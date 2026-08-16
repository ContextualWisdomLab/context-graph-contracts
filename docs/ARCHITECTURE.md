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
own their own storage, authorization, retries, and audit trails.

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

## Truth model

`authoritative`, `observed`, `inferred`, and `proposed` are not confidence
levels. They describe how an assertion entered the ecosystem. Confidence and
verification evidence belong in domain-specific payloads.

## Temporal model

`valid_from`/`valid_to` represent real-world validity. `recorded_at` and
`superseded_at` represent the system's knowledge interval. Consumers can
therefore reconstruct both "what was true" and "what was known at the time."

## Assertion model

A context assertion is the smallest graph fact this repository will validate.
It is a subject-predicate-object statement plus truth status, time, optional
provenance, and one or more context memberships. The object is an interchange
payload, not a row in a shared graph database.

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
                    │ provenance?             │
                    └───┬───────────────┬─────┘
                        │               │
            membership 0│               │membership 1
                        ▼               ▼
              analysis_run /     employment_group /
              workspace_record   other named context
```

Consumers should:

1. Parse the assertion and keep the supplied truth status.
2. Project the edge into their own store under their own identity.
3. Use every listed membership when interpreting the fact. A single group
   membership is never a complete social or organizational description.

`semantic-data-portal`, `enterprise-architecture-core`, LineageWeave, Orgmetra,
and `contextual-orchestrator` remain independently deployable. They share this
wire shape; they do not share tables.
