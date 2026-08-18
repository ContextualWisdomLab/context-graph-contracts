# ADR 0013: Keep external data-management frameworks behind neutral contracts

- Status: Accepted
- Date: 2026-08-18

## Context

Context Fabric needs to relate CWL-owned data-management capabilities, evidence, and assessment profiles to externally governed frameworks such as DAMA-DMBOK and DCAM. Those frameworks evolve independently of CWL and have publisher-controlled access and redistribution conditions. DAMA identifies the 2024 DAMA-DMBOK2 Revised Edition as the current revised second edition while separately developing DAMA-DMBOK 3.0. DAMA publishes selected images under CC BY-ND 4.0 but directs users to its licensing process for other DAMA-DMBOK content. EDM Association describes DCAM v3 as its current framework family and limits the framework, associated resources, and documentation to member use.

Copying publisher-owned definitions, diagnostic questions, scoring criteria, or evidence lists into this public package would create licensing and version-coupling risk. At the same time, inventing a second CWL truth-status, authority, or provenance vocabulary would weaken Context Fabric interoperability.

## Decision

1. `context-graph-contracts` publishes only framework-neutral interoperability grammar. It does not publish an assessment engine, framework catalog, workflow, authoritative capability store, or licensed framework profile.
2. An external framework is represented by publisher, version, official reference URI, license classification, and opaque external identifiers. `framework_version` remains an open bounded string so a publisher revision does not require a new wire schema merely to represent the version.
3. Capability names, definitions, scoring-dimension codes, and evidence-requirement codes in the public contract are independently authored CWL vocabulary. Publisher-owned framework prose, diagnostic questions, scoring rules, or evidence lists must not be copied into public package fields or fixtures.
4. Public mappings reuse the canonical CWL authority URI, truth-status, and provenance-reference schemas. A mapping or assessment cannot promote `observed`, `inferred`, or `proposed` evidence into authoritative truth.
5. Detailed publisher profiles, if CWL later has applicable rights, belong in access-controlled artifacts outside the public package with explicit export controls and version provenance.
6. `semantic-data-portal` remains the authority for Data/AI context evidence such as assets, glossary, lineage, domains, data products, trust, and certification. `enterprise-architecture-core` remains the authority for target capabilities, initiatives, transformations, and architecture decisions. This package only carries interoperable references between those authorities and a framework reference.

## Consequences

Consumers can map one CWL capability model to multiple external framework versions without moving authoritative business state into this repository. Framework upgrades remain data/profile changes unless the provider-neutral contract itself must evolve. Public package distribution stays independent of access to licensed framework content.

The contract cannot certify DAMA-DMBOK or DCAM conformance, maturity, membership, or endorsement. Such claims require the applicable publisher rules, licensed material, human governance, and product-owned assessment evidence.

## Verification

`tests/test_data_management_framework_schema.py` executes installed-package discovery, Draft 2020-12 schema validity, canonical authority/truth/provenance reuse, required official-reference metadata, bounded license classification, and rejection of unmodelled copied-body fields. The complete contract-bundle manifest and verifier include the packaged schema bytes, so a release candidate must also account for this resource in exact bundle evidence.

## References

DAMA International. (2024). *The DAMA guide to the data management body of knowledge (DAMA-DMBOK2R)* (2nd ed., rev.). Technics Publications.

DAMA International. (n.d.-a). *DAMA DMBOK revision*. Retrieved August 18, 2026, from https://dama.org/dama-dmbok-revision/

DAMA International. (n.d.-b). *DAMA-DMBOK®*. Retrieved August 18, 2026, from https://dama.org/dmbok2r-infographics/

EDM Association. (2025, June 30). *Announcing DCAM v3: Meet the new standard for your data*. https://edmcouncil.org/announcement/announcing-dcam-v3-meet-the-new-standard-for-your-data/

EDM Association. (n.d.). *Data management - DCAM*. Retrieved August 18, 2026, from https://edmcouncil.org/frameworks/dcam/
