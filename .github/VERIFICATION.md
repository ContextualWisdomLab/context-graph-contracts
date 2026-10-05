# Local verification — self-hosted CI migration

## Scope

Candidate branch: `ci-self-hosted-workflows`, stacked on existing #21 source
`a4538daee92f7062b547830ff5932a2a9f7d49c4`. This is not protected integration,
an immutable release, or consumer authority. Current repository `.github/`
directory is the migration scope; the organization's separate `.github`
repository was not modified.

## Current acceptance — October 5, 2026

- Published existing migration as Draft PR #29, stacked on #21. Remote source
  `d25fc5b0068e92276ec70cb01b000badff3c4ec4` includes inline pre-checkout
  candidate admission: unsupported forks fail instead of skipping every job.
  Six tuples exercised against five actual shells; independent review passed.
- Combined local follow-up with the executable SDK quickstart: Python
  **3.11–3.14 each 599 passed**; SDK statement/branch coverage remains **100%**.
  Ruff/actionlint pass. Quickstart executed from a real nonrepository cwd with
  the installed wheel's isolated interpreter; synthetic authority/media
  rejection and envelope/truth/time/provenance preservation succeeded.
- Quickstart independent review passed: four focused tests, scoped Ruff and
  separately isolated installed-wheel execution passed. All four reviewed file
  hashes match. No runtime package implementation or dependencies were changed.
- Remote inventory rechecked at 12:09–12:11 KST: proposed groups still absent,
  environments=0, repo-scoped runners=0, all four workflow identities disabled.
  Parent independently queried environments=0, rulesets=[] and disabled workflow
  identities. The old organization ruleset 18156473 in Issue #15 is historical,
  not current governance proof. Neither develop nor main has workflow source.
- PR checks labelled successful are **review skipped** (Draft / expired trial),
  not qualifying approval or CI evidence. No remote execution is claimed.

Next operation: publish the reviewed quickstart on the same Draft PR and bind
this exact consumer scope to the existing runner-owner issue
`ContextualWisdomLab/linux-cluster-ops#326`; do not borrow existing restricted
security/control runners or another consumer's pending approval.

## Historical migration checks (before follow-up)

- Baseline before edits: 565 tests passed, SDK coverage 100%.
- Python 3.11, 3.12, 3.13: full suite, **589 passed** per interpreter.
- Python 3.14: full suite, **589 passed**; coverage **1,837 statements and 552
  branches, zero missed/partial, 100%** across `cwl_context_contracts`.
- Repository-wide Ruff, actionlint (including ShellCheck), shell syntax and
  `git diff --check`: passed.
- Final migrated CI tests from a real nonrepository cwd: **80 passed**.
- Built and installed the real wheel into isolated `.package-smoke` and
  `.receipt-smoke` environments. Executed the five actual package/receipt
  workflow shell blocks: **5 passed**. The receipt smoke intentionally uses
  synthetic SPDX data; this is not a real Syft/security/provenance run.
- Installed conformance CLI: **63 cases, 7 profiles, zero failures**.
- Two fresh source copies built with uv 0.11.32 and identical source-derived
  `SOURCE_DATE_EPOCH`: wheel and sdist SHA-256 identities were byte-reproducible.

Matrix subprocesses unset inherited `PYTHONPATH`/`PYTHONHOME`; initial probes
otherwise imported the agent's Python 3.14 native dependencies under older
interpreters. No dependencies, application code or test expectations were
changed to bypass that environment mismatch.

## Regression and review evidence

- Observed runner/fork/release/temp policy RED before workflow changes.
- Signed runner-environment policy regressions retain hosted default denial,
  explicit self-hosted acceptance and missing/mismatched/unknown rejection.
- Independent helper review passed; signed DSSE identity and strict SPDX
  checks remain. Helper hashes were independently rechecked by the parent.
- First workflow review rejected persistent sibling build/evidence outputs.
  Actual workflow initialization now resets only its three owned output
  directories; regressions exercise stale contents twice while preserving
  source trees and unrelated files. Signing checkout now has an explicit SHA
  and a real HEAD equality guard before executing repository code.
- Corrected workflows passed independent bounded re-review: **28 focused tests**,
  actionlint and scoped Ruff passed. All four workflow hashes and all four
  helper hashes match the reviewed files. Model review is local quality evidence,
  not a qualifying GitHub approval or security audit.

## Not executed / remote prerequisites

No remote runner execution, GitHub qualifying approval, merge, tag or release
has occurred. Dedicated `CWL contracts CI` and `CWL contracts release` groups
were absent in the observed inventory. Existing workflow registry identities
were `disabled_manually`. No groups/runner permissions, workflow enablement,
repository protection/default branch or release environment settings were
changed. No hosted fallback is present.

The owner must provision isolated runners, configure repository-only group
access and independent main-only release-environment approval, re-enable the
workflow identities, then prove exact-source runs with actual runner names.
Issue #15's governance/restacking and immutable release gates remain open.
Issue #28's future procedural contracts were not fabricated or substituted by
this CI migration.
