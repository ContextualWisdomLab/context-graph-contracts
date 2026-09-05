# Product / Technical Gap Baseline

This file records code-current gaps that materially affect the Context Fabric contract product. It distinguishes shipped branch truth from active-stack evidence and keeps architectural debt actionable instead of burying it in PR prose.

## State model

- **Shipped/default-branch truth** means behavior present on the repository's current default branch. It is not automatically the program's accepted integration target.
- **Active PR** means implemented on an unmerged exact head and therefore not shipped.
- **Accepted architecture** means a documented responsibility or constraint that new code must follow.
- **Open** means a verified gap with an identified owner or correction path.
- **External governance** means this repository must fail closed until the owning administrative path changes state.

## Current baseline

| Area | State | Evidence / decision | Required next state |
| --- | --- | --- | --- |
| Contract-only product boundary | Accepted architecture | ADR 0001 and `docs/CONTEXT_MAP.md` define this repository as the provider-neutral interoperability contract bounded context. Runtime graph/catalog/workflow/EA persistence/UI authority is out of scope. | Keep implementation dependencies pointed inward to contract semantics; use consumer-owned ACLs for product concepts. |
| Minimal Shared Kernel | Accepted architecture | Canonical identity/authority, truth, temporal, provenance, CloudEvents/schema/AsyncAPI-facing contracts and conformance evidence are the allowed cross-product vocabulary. | Reject additions that introduce product-specific aggregates, repositories, workflow or persistence without an accepted ADR. |
| `src/cwl_context_contracts/data_management.py` | Accepted with guarded boundary | **ADR 0013** permits a reference **interoperability** DTO/schema/conformance surface for data-management assessment exchange. It is not a catalog, assessment workflow or **system of record**. | Preserve the current reference-only boundary; no repository, database, mutation workflow or product authority may migrate into this module. |
| Canonical Context Map and Ubiquitous Language | Active PR correction | These artifacts were absent from the top functional stack. `tests/test_ddd_architecture_fitness.py` now makes their presence and minimum content executable. | Integrate dependency-first after ancestors and governance gates; keep the tests as a permanent architecture-fitness gate. |
| Generic bucket / foreign implementation creep | Active PR prevention | The DDD fitness test forbids generic production directories and imports from known foreign CWL product implementation packages. | Expand only when a concrete new dependency/path class is observed; do not convert this into a broad source-text policy where executable dependency inspection is available. |
| Exact release evidence | Active PR stack | #18/#19 and ancestors add complete-bundle/package/SBOM/provenance/reproducibility admission on unmerged heads. | Revalidate every exact head after stack/base migration; predecessor GREEN does not transfer. |
| Solo-maintainer protected-PR review governance | External governance / open | Central owner path `ContextualWisdomLab/.github#772` owns the live organization rule whose bare `required_approving_review_count=1` is structurally unsatisfiable for the declared one-human-maintainer organization when no independent eligible reviewer is named. Self-approval and model/bot-as-human are forbidden. | Remove or replace only the impossible generic approval count at the central governance layer while preserving or strengthening deterministic required workflows, security/SAST, coverage, package/SBOM/provenance, exact-head binding, thread resolution, deletion/non-fast-forward protection and routine-bypass prohibition. Do not turn this governance defect into a request for fictional reviewer provisioning. |
| `main` integration/default governance | External governance / open | Program architecture requires `main` as intended integration/default. Fresh repository metadata still reports `default_branch=develop`; the protected-branch collection contains `develop` only, while `main@99cb5468ba3c15c5e79688f53dee74724fae2d13` remains unprotected. Central owner path `ContextualWisdomLab/.github#1137` owns the protect-main-first transition and the later effective `~DEFAULT_BRANCH` ruleset reread. | Protect `main` to the intended integration/release standard first, preserve `develop` protection during transition, then switch the repository default to `main`, immediately re-read effective rulesets and required workflows, and rebuild the PR stack from fresh protected `main` without transferring predecessor evidence. |

## DDD correction policy

Path/name changes are not performed solely for visual tidiness. A move must identify the owning bounded context, consumers/imports, schemas/events, packaging metadata, tests, workflows and compatibility impact first. The current package layout is narrow and contract-specific, so this baseline does not manufacture a rename project without evidence. New generic buckets or direct dependencies on foreign product implementations fail the architecture-fitness test immediately.

## Release statement

No entry in the active PR stack is commercial/release truth until it is integrated on the intended protected `main` exact head and all applicable CI, security, coverage, package, SBOM, provenance, reproducibility, review and release gates pass together. This baseline must not be used to imply certification, adoption or acquisition valuation evidence.
