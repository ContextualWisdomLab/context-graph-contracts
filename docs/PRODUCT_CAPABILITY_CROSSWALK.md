# Product Capability Crosswalk

`context-graph-contracts` is the **contract-only** interoperability layer of CWL Context Fabric. The crosswalk below prevents consumers from mistaking a reusable contract for an authoritative application or runtime.

| Buyer / ecosystem need | Owned here | Executable evidence | Out of scope / owning product |
| --- | --- | --- | --- |
| Canonical provider-neutral object identity | CWL canonical tenant/authority/object URI and UUIDv7 reference rules | JSON Schema, SDK parsers, fixtures, conformance tests | Object catalog and search belong to the relevant authoritative product |
| Context assertion exchange | Subject/predicate/object, truth status, bitemporal interval, provenance, memberships | `ContextAssertion`, assertion schema, positive/negative semantic profiles | Graph persistence/query and workflow are out of scope |
| Truth origin preservation | `authoritative`, `observed`, `inferred`, `proposed`, `superseded`, `rejected` wire semantics | SDK enums/parser checks and assertion conformance vectors | Deciding or promoting business truth belongs to the authoritative store/human-governed process |
| Bitemporal interoperability | Real-world validity and system-recorded interval semantics | Timestamp profile, interval schema, parser/formatter round trips | Temporal database storage/constraint implementation belongs to consumers such as Enterprise Architecture Core |
| Provenance reference | Provider-neutral provenance URI/reference shape and required provenance for authoritative/observed assertions | Schema, SDK validation, fixtures | Evidence storage and evidence access policy belong to the authoritative product |
| Event envelope interoperability | Provider-neutral CloudEvents fields/extensions and AsyncAPI component contract | CloudEvent schema, AsyncAPI, semantic negative/positive vectors | Broker topology, subscription runtime, retry queues and workflow orchestration are out of scope |
| Cross-language JSON exactness | Exact interoperable integer range and recursively validated JSON value contract | CWL JSON interoperability profile and installed-package smoke | Domain-specific higher-precision numeric encodings belong to higher-level contracts |
| SDK/resource distribution | Python reference SDK plus packaged schemas/contracts/fixtures/profiles and deterministic complete-resource byte identities | wheel/sdist package smoke, Python 3.11–3.14 CI, `cwl-context-bundle-manifest` over every explicitly published JSON resource | Language-specific generated SDKs beyond the released baseline require separately governed artifacts; digest evidence does not create trust or authorization |
| Supply-chain evidence | Package/SBOM/checksum generation and protected-main provenance/SBOM attestations | `supply-chain` workflow | Publication credentials, package-registry administration and downstream admission policy are out of scope |

## Context Fabric responsibility boundaries

- **Enterprise Architecture Core** owns authoritative business-capability/application/interface/technology/initiative/transformation/scenario state and its relational/bitemporal rules.
- **Semantic Data Portal** owns catalog assets, glossary, data products, contracts, trust/certification, graph/search/MCP projections and authoritative Data/AI context.
- **pg-erd-cloud** owns physical database/schema design evidence.
- **LineageWeave** owns inferred/proposed semantic lineage.
- **contextual-orchestrator** may propose context but cannot mutate authoritative stores through this contract.
- **naruon** and other products integrate through published API/event/package contracts rather than direct application-table SQL.

Any requested runtime graph store, catalog UI, workflow engine, Enterprise Architecture database, authorization service, or product-specific business mutation is **out of scope** for this repository even when it reuses these contracts.
