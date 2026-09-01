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
| PR #20 exact-head runner-contract lint | Active PR repair | Exact head `2d404783d31dcf577842df8e0996c97c09173d53` failed both Python 3.12 and 3.14 CI lanes after lock resolution, dependency sync and compile succeeded. Ruff reported only `D100` and `I001` at `tests/test_runner_image_contract.py:1`; the file was introduced by test commit `522ec85719b3fdd1356c0dd4411054180a79065b`. The package lane succeeded, so this is a repository-owned lint defect in the new test module rather than a product/runtime, provider, permission, dependency or central-workflow failure. | Commit `1898ec0023ac14ee83bc1e13c33be461af161383` adds the missing module docstring so Ruff can canonicalize the import block without changing runner-policy assertions. Require fresh exact-head CI success; predecessor failure or queued evidence is not passing. |
| Independent counted human approval | External governance / open | Central owner path `ContextualWisdomLab/.github#772` owns non-author human reviewer permission provisioning. Bot/status/self-approval is not equivalent. | Provision qualifying reviewer permissions and collect fresh approval on the unchanged integration candidate required by then-live policy. |
| `main` integration/default governance | External governance / open | Program architecture now requires `main` as intended integration/default. Repository metadata still reports `develop`; `main@99cb5468ba3c15c5e79688f53dee74724fae2d13` is currently unprotected while `develop` is protected. Central owner path `ContextualWisdomLab/.github#1137` was updated with the superseding acceptance. | Protect `main` with effective exact-head checks/reviews, thread/deletion/non-fast-forward controls and no routine bypass; switch coherent default/integration metadata; then rebuild the PR stack against the fresh live base without transferring predecessor evidence. |

## DDD correction policy

Path/name changes are not performed solely for visual tidiness. A move must identify the owning bounded context, consumers/imports, schemas/events, packaging metadata, tests, workflows and compatibility impact first. The current package layout is narrow and contract-specific, so this baseline does not manufacture a rename project without evidence. New generic buckets or direct dependencies on foreign product implementations fail the architecture-fitness test immediately.

## Release statement

No entry in the active PR stack is commercial/release truth until it is integrated on the intended protected `main` exact head and all applicable CI, security, coverage, package, SBOM, provenance, reproducibility, review and release gates pass together. This baseline must not be used to imply certification, adoption or acquisition valuation evidence.
