# Ubiquitous Language

These terms are normative for code, schemas, tests and documentation in `context-graph-contracts`. Product-specific meanings stay in the owning bounded context and must not be smuggled into this vocabulary through generic names.

| Term | Meaning in this bounded context |
| --- | --- |
| Object Reference | A provider-neutral, canonical reference to an object owned elsewhere. The identifier is UUIDv7-shaped where the published contract requires it; the reference does not imply that this library stores the object. |
| Authority | The named source that is entitled to assert or own a fact. Authority is explicit and must not be inferred from transport, caller identity or repository location. |
| Truth Status / Truth Origin | The declared epistemic state of a relationship or assertion, including authoritative, observed, inferred, proposed, superseded or rejected where the applicable contract permits it. Inferred/proposed data never becomes authoritative merely by crossing this contract. |
| Valid Time | The interval in which a fact is asserted to hold in the real world or business domain. |
| System Time | The interval in which a fact/version is recorded by an owning system. It is distinct from Valid Time. |
| Bitemporal Interval | A contract shape that preserves both Valid Time and System Time semantics without turning this package into a temporal database. |
| Provenance Reference | A portable reference to evidence describing where an assertion or artifact came from. It is evidence metadata, not authorization. |
| Context Assertion | A portable assertion connecting a subject to context with explicit authority, truth and temporal/provenance semantics. |
| Context Membership | A constrained membership assertion used by the published context-assertion contract. It does not establish application tenancy or caller authorization. |
| CloudEvent Envelope | The interoperable event envelope governed by the supported CloudEvents profile and the CWL timestamp/runtime-type rules. |
| Contract Bundle | The complete, versioned collection of schemas, conformance resources and related contract assets that a consumer admits together. |
| Conformance Evidence | Deterministic evidence that a candidate value or implementation was evaluated against the published semantic/schema profile. |
| Admission Receipt | Deterministic evidence recording the exact admitted contract/conformance identity. It is not a business approval or product authorization token. |
| Release Evidence | Package checksums, SBOM/provenance and attestation evidence that binds a distributable artifact to the verified source/release process. |
| Anti-Corruption Layer | Consumer-owned translation that keeps an owning product's domain model from leaking into the Shared Kernel. |
| Shared Kernel | The intentionally minimal cross-product vocabulary in this repository. Expansion requires proof that the concept must be identical across bounded contexts. |

## Data-management reference vocabulary

`src/cwl_context_contracts/data_management.py` and its schemas expose a reference interoperability model for exchanging data-management framework/assessment evidence. Under ADR 0013, this is **not** the system of record for catalogs, governance workflows, assessment lifecycle, portfolio decisions or remediation execution. Those facts remain in their owning products. The module may validate a portable contract but must not acquire repositories, persistence, product workflow or authority over those facts.

## Naming rules

Use domain terms above when they carry a defined invariant. Avoid catch-all names such as `utils`, `helpers`, `common`, `shared`, `core`, `models`, `services`, `misc` or `legacy` for new domain behavior. A technical helper that is genuinely local should be named for the contract responsibility it serves, and product-specific terms belong behind the consumer's Anti-Corruption Layer rather than in this package.
