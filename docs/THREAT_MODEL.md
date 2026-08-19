# Threat Model

## Scope

Context Graph Contracts is a **contract-only**, provider-neutral interoperability package. It defines canonical identifiers, timestamps, truth-origin and provenance semantics, CloudEvents/AsyncAPI/JSON Schema contracts, semantic conformance vectors, and reference SDK behavior. It is not a catalog, graph database, workflow engine, authorization service, Enterprise Architecture store, or UI.

This distinction is a security boundary: successful parsing or schema validation **does not authorize** an event, assertion, producer, consumer, tenant, state transition, external locator, or network access. Owning products must apply their own authenticated, purpose-bound authorization before changing authoritative state and their own outbound-network policy before dereferencing external locations.

## Assets to protect

- canonical UUIDv7 object identity and tenant/authority binding;
- explicit truth status (`authoritative`, `observed`, `inferred`, `proposed`, `superseded`, `rejected`);
- real-world validity and system-recording timestamps;
- provenance references and byte-identity digests;
- CloudEvents metadata and typed assertion membership semantics;
- portable semantic conformance profiles used by non-Python consumers;
- package, SDK, schema, and release provenance.

The contract layer intentionally avoids credentials, passwords, tokens, DSNs, raw personal attributes, and source payloads. When personal or sensitive data is needed by a product, that data remains in the owning system and is referenced through authorized opaque identifiers.

## Trust boundaries

1. **Producer to contract consumer.** Every wire value is untrusted until structural and semantic conformance succeeds. Schema validation alone is insufficient when an invariant requires semantic validation.
2. **Tenant and authority boundary.** Canonical asset references bind tenant, authority, object type, and UUIDv7 identity. Same-tenant invariants apply to event source/subject, membership, edge, and provenance relationships where the profile requires them.
3. **Truth-origin boundary.** `inferred` or `proposed` output is not equivalent to authoritative fact. A consumer must preserve truth origin and apply its own governed promotion process.
4. **Runtime authorization boundary.** The package has no identity provider, policy engine, database session, or ambient authority. Consumers must verify issuer, audience, tenant, role, purpose, signature, and application policy independently.
5. **External-reference boundary.** A framework `official_reference_uri` is untrusted metadata, not fetch authority. The public contract requires a canonical HTTPS location, but HTTPS syntax does not prove publisher ownership, DNS safety, content integrity, or permission to dereference it.
6. **Package/release boundary.** Generated schemas, SDK behavior, semantic vectors, package metadata, SBOM/provenance, and published artifacts must correspond to one exact reviewed source head.

## Threats and controls

| Threat | Contract-layer control | Consumer obligation |
| --- | --- | --- |
| Cross-tenant reference confusion | Canonical URI parsing and same-tenant semantic checks reject contradictory producer/subject, membership, edge, and provenance relationships covered by the profile. | Bind authenticated tenant context to the owning command/query boundary; never infer authorization from URI syntax. |
| Truth laundering | Truth status remains explicit and conformance rejects unsupported values. | Do not silently promote `inferred` or `proposed` facts to `authoritative`; record the authorized transition and evidence in the owning product. |
| Timestamp ambiguity or impossible civil time | CWL Timestamp Profile v1 defines canonical RFC 3339 semantics; reference parsing and portable semantic vectors reject impossible or non-profile values. | Non-Python consumers must run the semantic profile or refuse conformance if their JSON Schema implementation only annotates `format`. |
| Numeric precision loss across languages | CWL JSON interoperability profile accepts integer values only in the exact interoperable range where numeric identity is portable. | Higher-level domain contracts must use an explicit typed/string representation when a larger exact integer is required. |
| Duplicate or contradictory assertion membership | Semantic assertion conformance enforces membership uniqueness and tenant/subject invariants that structural JSON Schema cannot express portably. | Run the semantic conformance profile, not only structural schema validation. |
| CloudEvent metadata injection | Core attributes are type-checked; `source`, `subject`, `tenantid`, `dataschema`, time, and event data are semantically constrained. | Apply application authorization and signature/trust policy after conformance. |
| Unsafe external framework locator / SSRF handoff | Framework `official_reference_uri` is required and structurally restricted to lowercase `https://` locations even when a JSON Schema implementation treats `format` as annotation. Non-HTTPS schemes such as `http`, `javascript`, and `data` fail closed. | Treat the locator as display/reference metadata. Do not automatically fetch it. Any product that deliberately dereferences it must enforce its own DNS/IP allow/deny policy, redirect limits, response-size/time bounds, content validation, and connector SSRF controls. |
| Credential or PII exfiltration in envelopes | Contract documentation forbids credentials, DSNs, tokens, passwords and unnecessary raw personal data in context bundles. | Keep secret and PII values in the owning product, expose only purpose-authorized references, and audit exports. |
| Resource exhaustion | Event payload traversal rejects excessive nesting, non-string map keys, non-finite numbers, cycles and Python-only values. Approved conformance-manifest verification reads at most 1 MiB plus one sentinel byte before UTF-8/JSON parsing and fails closed on larger input. | Impose transport/body size, rate, concurrency and memory limits appropriate to the hosting service. |
| Replay or replay storm | Event identity and time/provenance fields remain explicit and stable; the contract does not treat duplicate receipt as a new authoritative fact. | Consumers must implement idempotency, replay windows, deduplication and bounded retry at their durable event boundary. |
| Graph/Cypher injection | No graph query runtime or Cypher execution exists in this package. | A graph-owning product must use typed parameters and traversal bounds; never expose raw model-authored queries merely because identifiers are conformant. |
| Prompt-injection policy mutation | No LLM or policy mutation runtime exists here; model output can be represented only with its explicit truth origin. | Owning products must keep deterministic authorization/security gates independent of model judgment and require explicit promotion for proposals. |
| Supply-chain substitution | Release gates require exact-source CI, package smoke tests, schema/conformance evidence, SBOM/provenance and artifact/source hash verification before publishing. | Pin and verify the released version/digest required by the consuming product. |

## Abuse cases that must fail closed

- a producer reference names tenant A while event subject or redundant tenant metadata names tenant B;
- two memberships use the same `context_ref` while attempting different levels;
- an RFC 3339-looking timestamp encodes an impossible calendar date or a formatter would emit a non-profile sub-minute offset;
- event data contains a non-finite number, cyclic container, excessive nesting, non-string key, or exact integer outside the portable interoperability range;
- `dataschema` is not an absolute URI;
- a framework official reference uses a non-HTTPS scheme such as `http:`, `javascript:`, or `data:`;
- an assertion requiring same-tenant provenance points to another tenant;
- an approved conformance-manifest file exceeds the verifier's 1 MiB input ceiling;
- a consumer attempts to treat schema success as identity, role, purpose or policy authorization;
- a consumer treats an HTTPS framework locator as permission to perform an outbound fetch without its own SSRF controls;
- replay of the same event is interpreted as permission to create a second authoritative fact;
- a context bundle attempts to carry credentials, passwords, access tokens or DSNs.

## Out-of-scope runtime controls

Database RLS, service authentication, Keyverse OIDC verification, connector SSRF protection, durable replay stores, graph traversal execution, retention enforcement and UI authorization are intentionally not implemented in this package. Their absence must not be papered over by adding runtime authority to Context Graph Contracts. Each owning CWL product must implement and test those controls at its own boundary while consuming these versioned contracts.

## Change rule

Any change that adds a wire field, truth status, identity rule, semantic invariant, event extension, schema profile, SDK serialization behavior, generated artifact or release channel must update this threat model when the attack surface changes and add executable structural or semantic negative vectors at the same boundary. Security prose is not proof; exact source, tests, conformance artifacts and release provenance remain the implementation evidence.
