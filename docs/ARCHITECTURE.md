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

## Authority model

The `authority` URI segment names the system permitted to accept commands for an
object. A read model may project another authority's object but must not reuse
that authority's URI for a locally inferred object.

## Truth model

`authoritative`, `observed`, `inferred`, and `proposed` are not confidence
levels. They describe how an assertion entered the ecosystem. Confidence and
verification evidence belong in domain-specific payloads.

## Temporal model

`valid_from`/`valid_to` represent real-world validity. `recorded_at` and
`superseded_at` represent the system's knowledge interval. Consumers can
therefore reconstruct both "what was true" and "what was known at the time."
