# Context Graph Contracts Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the first independently testable CWL context-contract baseline.

**Architecture:** JSON Schema resources define the language-neutral wire format. A dependency-free Python package implements the same invariants and provides executable conformance fixtures.

**Tech Stack:** Python 3.11-3.14, JSON Schema Draft 2020-12, CloudEvents 1.0.2, pytest, coverage.py, uv.

## Global Constraints

- The repository remains contract-only.
- Canonical identifiers require RFC 9562 UUIDv7.
- Production statement and branch coverage remain 100%.
- Public APIs require docstrings.

---

### Task 1: Canonical identity and truth vocabulary

**Files:** `src/cwl_context_contracts/identity.py`, `truth.py`, and their tests.

- [x] Write failing tests for URI round trips and invalid UUID/segments.
- [x] Implement exact canonical URI parsing and construction.
- [x] Add the six-value truth-status enum.
- [x] Run focused tests and commit.

### Task 2: Temporal and provenance contracts

**Files:** `temporal.py`, `provenance.py`, and their tests.

- [x] Write tests for timezone-awareness and exclusive end points.
- [x] Implement bitemporal validation and query helpers.
- [x] Implement SHA-256 evidence references.
- [x] Run focused tests and commit.

### Task 3: CloudEvents and schemas

**Files:** `events.py`, packaged schemas, fixtures, and schema tests.

- [x] Add valid and invalid structured-event fixtures.
- [x] Implement core and extension validation.
- [x] Validate schemas against Draft 2020-12.
- [x] Run full coverage and package checks.

### Task 4: Governance documentation

**Files:** README, ADRs, doctoring, security, changelog, and CI.

- [x] Document authority, truth, time, and compatibility boundaries.
- [x] Pin GitHub Actions by immutable SHA.
- [x] Run final validation and open a draft PR.

### Task 5: Typed assertion and lock reproducibility

**Files:** `assertion.py`, interval/provenance mappings, schemas, fixtures, lockfile.

- [x] Add context-assertion and membership contracts with consumer-shaped tests.
- [x] Add interval and provenance wire mappings plus RFC 3339 helpers.
- [x] Commit `uv.lock` and switch CI to `uv lock --check`.
- [x] Trace RFC 3339, bitemporal, PROV-DM, RDF, and multilevel-membership sources.
