# Repository-owned GitHub Actions

All repository-owned workflow definitions, CI-only helpers and CI policy tests
live here. `src/` remains the runtime-independent contract SDK; application
contract tests remain in `tests/`. This change does **not** centralize execution
in the separate `ContextualWisdomLab/.github` repository and does not modify its
required security/review workflows or organization settings.

## Candidate basis and boundaries

The CI migration is stacked on the existing #21 candidate (`a4538da`) rather
than replacing the root #4 owner branch. PRD P0 contract behavior, exact source
SHA checkout, Python 3.11–3.14, Ruff, 100% statement/branch coverage,
installed-wheel checks, semantic conformance, package/SBOM identity and
reproducibility remain required. Issue #15 owns protected integration/release
acceptance. Issues #26–#28 describe future contract-owner work, not implemented
or released capabilities. Root #4 and #21 have diverged; reconcile the latest
root truth-retention/governance changes dependency-first before integration.
No sibling feature branch becomes consumer release authority.

## Runner routing (prepared, not provisioned)

| Workflow/job | Proposed runner group | Labels |
| --- | --- | --- |
| `ci` test (4 versions), package | `CWL contracts CI` | `self-hosted, Linux, X64, cwlab` |
| `receipt-package-smoke` installed-wheel | `CWL contracts CI` | same |
| `reproducibility` release-package-reproducibility | `CWL contracts CI` | same |
| `supply-chain` package-evidence | `CWL contracts CI` | same |
| `supply-chain` attest-protected-main | `CWL contracts release` | same |

These groups did not exist in the inspected organization inventory. Existing
Default was empty; security/control/GPU/health groups have distinct ownership
and restrictions. Do not move those runners, broaden their allowlists or
silently fall back to hosted infrastructure. Provision dedicated, disposable
Linux x64 runners with this repository-only access through the runner owner.
Require a fresh VM/container boundary per job, no production network access,
no host Docker socket or mounted credentials, and no reuse of PR workspaces by
signing jobs. Fork guards are defense in depth, **not** isolation. PRs from
forks are not executed by these lanes and skipped checks are not acceptance.

Provision Git, Bash, GNU checksum tools, supported Node for pinned JavaScript
actions, Python setup tooling, and GitHub CLI with artifact-attestation support.
Pinned setup actions select Python and uv; Syft remains pinned by the SBOM job.
Host labels describe placement, not an attested OS image or toolchain.

## Signing is separately gated

`attest-protected-main` requires a push to protected `main`, the separately
configured `contracts-release` GitHub environment and an explicitly enabled
repository variable `CONTRACTS_SELF_HOSTED_RELEASE_ENABLED=true`.
The owner must configure required independent environment approval and restrict
its deployment branches to `main` **before** enabling the variable. Workflow
YAML cannot create those protection rules. A skipped signing lane, an unset
variable or an absent environment configuration is **not** release evidence.

The migrated verifier defaults to the historical `github-hosted` policy;
self-hosted callers must explicitly select `EXPECTED_RUNNER_ENVIRONMENT`.
The signed SLSA runner environment must match that choice. Exact repository,
source SHA/ref, signer workflow/digest, OIDC issuer, signed DSSE subject and
SPDX predicate checks remain mandatory. Removing the hosted-only CLI flag for
this explicit self-hosted policy is not a SLSA-level claim or release approval.
Consumers must independently approve operator-managed runner trust.

## Local checks

Use the repository's required uv version, not a floating local installation:

```sh
uvx --from uv==0.11.32 uv sync --frozen --extra dev --python 3.14
.venv/bin/python -m ruff check .
.venv/bin/python -m coverage run -m pytest -q tests .github/tests
.venv/bin/python -m coverage report
actionlint .github/workflows/*.yml
```

`pyproject.toml` includes `.github/tests` in normal pytest discovery. Custom
runner labels are declared in `actionlint.yaml`, not suppressed from lint.
CI helpers can be invoked by absolute path from outside the checkout.

## Remote completion checklist

- [ ] Dedicated CI/release groups provisioned with verified isolation and access.
- [ ] Existing disabled workflow identities re-enabled by the authorized owner.
- [ ] Exact-head runs show real matching `runner_name` values and terminal success.
- [ ] Python matrix, wheel smoke, real Syft SBOM and double-build evidence succeed.
- [ ] Protected/default-main and qualifying review prerequisites from #15 converge.
- [ ] Approved release environment configured; self-hosted release trust accepted.
- [ ] Exact protected-main signing and independent consumer verification succeed.

Local passes, remote job execution, qualifying independent approval, merge and
immutable publication are distinct gates. No tag, release or protection bypass
is authorized or performed by this migration.
