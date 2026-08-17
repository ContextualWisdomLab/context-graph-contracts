# Context Graph Contracts

Context Graph Contracts is the shared, versioned interoperability layer for
ContextualWisdomLab products that exchange **context**, **lineage**,
**architecture**, and **impact-analysis** facts.

Independent systems use these contracts to name the same objects, say how an
assertion entered the ecosystem, and point at evidence — without sharing a
database or surrendering domain authority.

## What this is not

This repository is not a graph database, data catalog, enterprise-architecture
application, message broker, or workflow engine. It does not store entities,
run queries, host a UI, or own a runtime topology.

It publishes versioned schemas, a reference Python package, and compatibility
rules. Owning products keep their own stores, authorization, retries, and
audit trails.

## Contract baseline

Operators and integrators can rely on these interchange rules.

**Producer authority URI.**
`urn:cwl:{tenant_id}:{authority}` names the system allowed to accept commands
for an object. In a CloudEvent this value is `source`.

**Canonical asset URI.**
`urn:cwl:{tenant_id}:{authority}:{object_type}:{uuidv7}` is the stable identity
of the object being discussed. In a CloudEvent this value is `subject`.

**Truth status.**
Every cross-domain assertion carries one of `authoritative`, `observed`,
`inferred`, `proposed`, `superseded`, or `rejected`. These values describe
origin, not confidence. Consumers must not promote `observed`, `inferred`, or
`proposed` assertions to `authoritative`.

**Bitemporal validity.**
Real-world validity (`valid_from` / `valid_to`) stays distinct from
system-recording time (`recorded_at` / `superseded_at`). Open intervals use
`null` on the wire; they do not use sentinel dates.

**Timestamp profile.**
CWL Timestamp Profile v1 is an explicitly named, leap-second-free subset of
RFC 3339 used by the temporal and event contracts. JSON Schema provides the
structural and lexical gate; consumers must also execute the packaged semantic
conformance vectors so impossible calendar values cannot pass merely because
`format` is annotation-only.

**Provenance.**
A material assertion can point to a source asset and a SHA-256 digest of the
exact evidence bytes. A digest proves byte identity, not trust or
authorization.

**Context assertion.**
A typed subject-predicate-object assertion carries truth status, bitemporal
validity, optional provenance, and one or more context memberships. Packaged
semantic vectors cover cross-field rules that JSON Schema cannot express
portably, including same-tenant references, non-self edges, and unique context
memberships.

**Service events.**
Notifications use CloudEvents 1.0.2 structured JSON. `source` and `subject`
share one tenant. Event IDs are UUIDv7. `dataschema` remains a core
CloudEvents attribute. Payloads accept only finite, acyclic, bounded
JSON-native values and interoperable integers in the exact range required by
the CWL JSON interoperability profile.

The published surface is JSON Schema Draft 2020-12 plus AsyncAPI 3.1.0
reusable components for the shared CloudEvent and Context Assertion payloads.
The AsyncAPI document does not define servers, channels, operations, broker
addresses, or runtime topology.

The Python reference package exposes `load_schema()`, `load_contract()`,
`ContextAssertion`, and packaged conformance profiles and fixtures. These
artifacts do not grant a consumer authority to mutate another product's store.

## Verify an installed package

Run the exact semantic vectors shipped inside the installed package before
accepting it as a compatible Context Fabric contract implementation:

```console
$ cwl-context-conformance
{"case_count": 31, "failures": [], "profile_count": 4, "status": "pass"}
```

The command exits non-zero and identifies the exact profile/case when a vector
is accepted, rejected, or canonicalized differently from the published
contract. Python callers can use `run_packaged_conformance()` for evidence or
`assert_packaged_conformance()` for a fail-closed gate. This verifies the
installed reference SDK and its packaged semantic resources; it does not grant
runtime authority or prove another implementation conformant unless that
implementation executes equivalent vectors itself.

Capture the exact semantic-resource identity alongside the conformance result:

```console
$ cwl-context-conformance-manifest
{"algorithm":"sha256","distribution_name":"cwl-context-contracts","distribution_version":"0.1.0","manifest_format":"cwl-context-conformance-manifest/v1","profile_count":4,"profiles":[...]}
```

The manifest identifies the installed distribution name/version and hashes the
exact bytes of every packaged semantic profile in stable profile-name order.
Store that JSON with CI/release evidence so an operator can distinguish “the
conformance command passed” from “this exact package version and these exact
published vectors passed.” If either `distribution_version` or a profile digest
differs from the version/digest approved by the consuming product, stop the
integration and reconcile the contract release before accepting Context Fabric
data. Python callers can use `build_packaged_conformance_manifest()` or
`conformance_profile_sha256()` for the same evidence. SHA-256 here proves byte
identity only; package provenance, authorization, and trust remain separate
gates.

Given a manifest captured and approved through the consuming product's release
process, compare it with the installed package before enabling the integration:

```console
$ cwl-context-conformance-verify approved-conformance-manifest.json
{"installed_distribution_name":"cwl-context-contracts","installed_distribution_version":"0.1.0","mismatches":[],"next_action":"accept the installed conformance evidence","verification_format":"cwl-context-conformance-verification/v1","verified":true}
```

Exit `0` means the approved package version and every approved semantic-profile
digest match the installed evidence. Exit `1` means version/profile evidence
drifted; use the emitted mismatch identities to install the approved package or
approve a newly reviewed exact manifest. Exit `2` means the approved manifest
cannot be read or parsed as a JSON object. The verifier does not decide who may
approve a manifest and does not replace signature, provenance, SBOM, or runtime
authorization gates. Python callers can use
`verify_packaged_conformance_manifest()` for the same deterministic decision.

For deployment admission, prefer the composite command so semantic execution
cannot accidentally be omitted when checking approved profile bytes:

```console
$ cwl-context-conformance-admit approved-conformance-manifest.json
{"admission_format":"cwl-context-conformance-admission/v1","admitted":true,"installed_distribution_name":"cwl-context-contracts","installed_distribution_version":"0.1.0","manifest_verification":{"installed_distribution_name":"cwl-context-contracts","installed_distribution_version":"0.1.0","mismatches":[],"next_action":"accept the installed conformance evidence","verification_format":"cwl-context-conformance-verification/v1","verified":true},"next_action":"verify artifact provenance and runtime authorization before enabling the integration","semantic_conformance":{"case_count":31,"failures":[],"profile_count":4,"status":"pass"}}
```

Admission requires both the installed semantic suite and the exact
approved-manifest comparison to pass. A positive result is intentionally not a
signature, provenance decision, review approval, or authorization grant; verify
those owning gates before enabling the integration. Python callers can use
`evaluate_packaged_conformance_admission()` for the same composition.

## Who consumes these contracts

`semantic-data-portal`, `enterprise-architecture-core`, `pg-erd-cloud`,
`LineageWeave`, and `contextual-orchestrator` exchange contracts or events and
keep their own authoritative state. They do not read one another's databases.

## Further reading

- Architecture and identity, truth, and temporal models: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Accepted decisions: [`docs/adr/`](docs/adr/)
- Bibliographic sources: [`docs/doctoring/REFERENCES.md`](docs/doctoring/REFERENCES.md)
- Local development: [`CONTRIBUTING.md`](CONTRIBUTING.md)