# ADR-0001: Data-management framework boundary

## Status

Proposed

## Context

ContextualWisdomLab needs a common way to relate data-management responsibilities, evidence, assessments, and improvement actions to external professional frameworks. DAMA-DMBOK is useful as a body-of-knowledge reference, while DCAM is useful as a capability-assessment reference. Their published and licensed materials have different redistribution constraints.

CWL already separates authoritative domain records from shared interoperability contracts. This repository therefore must not become a copy of any external framework or a central business-data system of record.

## Decision

1. `context-graph-contracts` owns only framework-neutral interoperability contracts.
2. External frameworks are represented by references containing publisher, version, official URI, and license classification.
3. CWL capability definitions are original CWL definitions. Public schemas may carry opaque external references, but must not reproduce licensed framework prose, diagnostic questions, scoring criteria, or evidence lists.
4. Detailed licensed profiles, if acquired, must be stored outside public artifacts with access and export controls.
5. Evidence records retain their source authority and provenance. An assessment result cannot upgrade `observed`, `inferred`, or `proposed` evidence into an authoritative business fact.
6. Framework version and CWL contract version evolve independently.
7. `semantic-data-portal` is the natural authority for data-context evidence such as assets, glossary, ownership, stewardship, quality, lineage, and certification. `enterprise-architecture-core` is the natural authority for target capabilities and improvement initiatives. Domain repositories remain authoritative for their own business facts and controls.

## Consequences

- A future DMBOK or DCAM revision can be mapped without changing CWL domain identifiers.
- Public packages remain usable without requiring redistribution rights to licensed framework content.
- Assessment engines can support additional frameworks through profiles rather than hard-coded framework-specific logic.
- A private framework-profile repository is only justified after CWL has a license requiring restricted storage of detailed mappings.

## Verification

Conformance tests must reject public fixtures that embed restricted framework prose and must validate license classification, framework version, evidence authority, and provenance fields.

## References

DAMA International. (2024). *The DAMA guide to the data management body of knowledge (DAMA-DMBOK2R)* (2nd ed., rev.). Technics Publications.

EDM Council. (2025, June 30). *Announcing DCAM v3: Meet the new standard for your data*. https://edmcouncil.org/announcement/announcing-dcam-v3-meet-the-new-standard-for-your-data/
