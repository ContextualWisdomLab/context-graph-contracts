# Context Fabric product and technical gap baseline

This ledger records executable gaps for `ContextualWisdomLab/context-graph-contracts`. It is not release evidence and must not promote mutable pull-request state into protected truth.

## Product boundary

`context-graph-contracts` is the contract-only Shared Kernel for canonical object and authority references, the six truth/origin dispositions (`authoritative`, `observed`, `inferred`, `proposed`, `superseded`, `rejected`), bitemporal semantics, provenance, Context Assertion, CloudEvents, JSON Schema/AsyncAPI, conformance/admission and generated/package evidence. It does not own a catalog, graph store, workflow engine, EA database, application runtime, product verdict or UI.

Product-domain truth remains with the producing bounded context. A consumer retains producer authority, event identity, schema/profile/admission version and provenance; it does not convert analysis, risk or model output into another context's authoritative fact.

## Current integration and evidence gaps

The intended integration/release authority is protected `main`. Live repository governance has not completed that migration: the repository still reports `develop` as default and `main` is not yet protected. Organization ruleset repair and default-branch migration therefore remain central control-plane dependencies. No ordinary product merge or release may use routine administrator bypass, self-approval, a synthetic reviewer, or stale approval/check evidence.

The dependency-root pull request has repaired a repository-owned source-integrity defect in CI and supply-chain workflows. Pull-request jobs now bind checkout and explicit post-checkout verification to the exact source expression, and PR dependency/package artifact names use that same source identity. Predecessor evidence is non-passing after any head or base movement. Repository-owned workflows still require live exact-head materialization and terminal execution before they count as GREEN.

The first immutable release remains outstanding. Release authority requires one exact integrated protected `main` source revision with package/install smoke, schema and semantic conformance, SBOM, provenance/attestation, reproducibility where applicable, rollback documentation and release artifacts bound to that same identity.

## Context Assertion and consumer boundary

The Context Assertion successor binds assertion data to one structured CloudEvent envelope and must preserve canonical `id`, `source`, `specversion`, `type`, `time`, `subject`, authority/truth, valid/business time, system-recorded time and typed provenance while rejecting hostile identity, media-type, type/dataschema and provenance mismatches. That work remains mutable until rebuilt on the protected integration line and published as an immutable release.

`ContextualWisdomLab/enterprise-architecture-core` may consume only a released compatible contract through an ACL. Its Quarantine Sandbox Runtime projection must remain provisional until the same protected CGC release supplies compatible schema/profile/admission/conformance evidence.

`ContextualWisdomLab/quarantine-sandbox-runtime` remains an independently deployable producer. It owns hostile-workload isolation, application-service lifecycle/resource/cleanup/attestation and artifact-analysis evidence. Its malware or artifact-risk analysis never becomes authoritative EA architecture truth merely by crossing this Shared Kernel.

## Next executable closure

1. Central owner establishes protected `main`, changes the default only after protection is verified, and re-evaluates effective `~DEFAULT_BRANCH` rules.
2. Central owner removes only the solo-maintainer-impossible bare approval count/routine bypass while preserving deterministic required workflows, security, thread resolution, deletion and non-fast-forward protection.
3. Rebuild the contract stack dependency-root first without transferring predecessor evidence; reacquire exact-source CI/security/package/SBOM/provenance evidence on every moved head.
4. Complete and verify the Context Assertion/CloudEvent admission contract, package interfaces and positive/hostile fixtures on the rebuilt line.
5. Publish the first immutable release from protected `main`; only then may enterprise-architecture-core or Quarantine Sandbox Runtime integrations claim released Context Assertion projection compatibility.
