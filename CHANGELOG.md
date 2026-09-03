# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Changed

- README is now a customer and operator page; local test commands live in
  `CONTRIBUTING.md`.
- ADRs 0001–0005 now include Context, Decision, Consequences, and APA 7th
  references for the standards this product already claims.
- UUIDv7 wire identities now fail closed on non-canonical text rather than
  silently normalizing spellings that the published JSON Schemas reject.
- Parser and adapter truth guards now preserve the supplied truth status
  exactly. A consumer can no longer reinterpret an observed, inferred,
  proposed, superseded, or rejected assertion as a different origin or owner
  disposition; owning products issue a new assertion or event when recording a
  new disposition. The retained `truth_status_rank()` ordinal is compatibility
  metadata only and is not an authorization or transition rule.
- Bitemporal open intervals now have one canonical producer shape across
  runtime, JSON Schema guidance, fixtures, and documentation: `valid_to` and
  `superseded_at` are omitted while open. Existing v1 payloads that used the
  previously accepted explicit JSON `null` remain admissible to consumers and
  are normalized to omission on serialization, preserving the repository's
  backward-compatibility rule without emitting two canonical encodings.
- Approved conformance-manifest verification now reads at most 1 MiB plus one
  sentinel byte before UTF-8/JSON parsing and fails closed with
  `approved_manifest_too_large` for oversized untrusted input.

### Added

- Canonical tenant-scoped producer authority URI contract.
- Canonical UUIDv7-backed CWL asset URI contract.
- Truth-status vocabulary separating authoritative, observed, inferred,
  proposed, superseded, and rejected assertions.
- Bitemporal interval and provenance-reference contracts.
- CloudEvents 1.0.2 structured-event reference implementation with UUIDv7
  event identity, producer-authority `source`, asset `subject`, and optional
  core `dataschema` support.
- Tenant-consistency validation between CloudEvents producer `source`, asset
  `subject`, and an optional `tenantid` extension.
- Fail-closed structured-event validation for non-string core attributes,
  non-finite numbers, non-string JSON keys, cyclic containers, non-JSON Python
  values, payload nesting deeper than 64 levels, and integers outside the RFC
  8259 exact interoperable range `[-(2**53)+1, (2**53)-1]`.
- JSON Schema Draft 2020-12 resources and positive/negative conformance
  fixtures.
- Provider-neutral semantic conformance profiles for the CWL Timestamp Profile,
  Context Assertion cross-field invariants, CloudEvent cross-field semantics,
  and exact JSON integer exchange; installed-package smoke tests execute the
  same vectors consumers receive.
- Buyer-executable `cwl-context-conformance` command plus
  `run_packaged_conformance()` / `assert_packaged_conformance()` APIs that emit
  exact profile/case evidence and fail closed for missing, malformed, or
  unregistered packaged profiles.
- Artifact-bound semantic evidence through
  `cwl-context-conformance-manifest`, `build_packaged_conformance_manifest()`,
  and `conformance_profile_sha256()`, binding release evidence to the installed
  `cwl-context-contracts` distribution version and the exact packaged bytes of
  every published conformance profile.
- Fail-closed `cwl-context-conformance-verify` command and
  `verify_packaged_conformance_manifest()` API that compare an independently
  approved manifest with the installed package, identify exact version/profile
  drift, and return an operator next action without inventing manifest-approval
  authority.
- Composite `cwl-context-conformance-admit` command and
  `evaluate_packaged_conformance_admission()` API that require both installed
  semantic conformance and an exact approved-manifest match while explicitly
  leaving artifact provenance, review policy, and runtime authorization to
  their owning gates.
- Deterministic `cwl-context-conformance-receipt` command and
  `build_packaged_conformance_admission_receipt()` API that normalize profile
  evidence by ascending `profile_name`, apply RFC 8785 canonicalization, bind
  approved-manifest semantics and complete admission evidence to separate
  SHA-256 identities, reject ambiguous/non-JCS-safe manifest shapes, and
  smoke-test the installed wheel without creating signature, trust, approval,
  provenance, or runtime authority.
- Deterministic `cwl-context-bundle-manifest` command and
  `build_packaged_contract_bundle_manifest()` API that bind the installed
  distribution version to SHA-256 identities for every explicitly published
  AsyncAPI document, JSON Schema, conformance fixture, and semantic profile in
  stable resource-path order; installed-wheel smoke verifies the command while
  leaving semantic conformance, package provenance, and runtime authorization
  as separate owning gates.
- Fail-closed `cwl-context-bundle-verify` command and
  `verify_packaged_contract_bundle_manifest()` API that rebuild the installed
  complete resource manifest and compare it with independently approved
  distribution/resource evidence, reporting exact missing, unexpected, and
  digest-different resource paths while reusing the bounded strict approved-JSON
  input boundary; installed-wheel smoke executes the verifier end to end.
- Repository architecture, security, testing, doctoring, and ADR baseline.
- Typed context-assertion contract with subject-predicate-object identity,
  non-promotable truth status, bitemporal validity, optional provenance, and
  multilevel context memberships.
- Wire mappings for bitemporal intervals and provenance references.
- CWL Timestamp Profile v1 parse/format helpers, with pre-release RFC3339-named
  aliases retained for compatibility; serialization rejects timezone offsets
  that cannot be represented by the profile.
- Committed `uv.lock` and lock-checked CI so consumer installs are reproducible.
- Exact-head SPDX JSON SBOM and SHA-256 package evidence on pull requests and
  protected-main builds, plus protected-main SLSA build-provenance and SBOM
  attestations using immutably pinned GitHub/Anchore actions.
- APA 7th doctoring for RFC 3339, RFC 8259, TSQL2/bitemporal semantics, PROV-DM,
  RDF 1.1, and multilevel-membership research.
- Executable documentation consistency tests bind advertised Python support and
  buyer-facing conformance claims to package and project metadata.
- A contract-only threat model with executable documentation checks that keeps
  runtime authorization, graph execution, durable replay, and connector policy
  in their owning products instead of inventing authority in the contract layer.
