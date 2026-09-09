# Context Graph Contracts Development Context

This repository is the provider-neutral contract layer for the CWL Context
Fabric. Follow `AGENTS.md` and the accepted ADRs.

Do not:

- add a catalog, graph store, workflow engine, or user interface;
- duplicate domain entities owned by `semantic-data-portal` or
  `enterprise-architecture-core`;
- treat inferred lineage as an audited fact;
- expose credentials, DSNs, personal data, or source payloads in event
  envelopes.
