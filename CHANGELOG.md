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
- Approved conformance-manifest verification now reads at most 1 MiB plus one
  sentinel byte before UTF-8/JSON parsing and fails closed with
  `approved_manifest_too_large` for oversized untrusted input.
- Downloaded package-evidence verification now bounds `SHA256SUMS` at 64 KiB
  and SPDX JSON at 16 MiB plus one sentinel byte, rejects duplicate JSON object
  members and Python-only non-finite constants, requires UTF-8 metadata, and
  reports post-check artifact read failures as structured mismatches instead of
  allowing untrusted evidence I/O to escape the verification boundary.
- Protected-main custom SPDX attestation verification now derives semantic
  identity from the exact signed in-toto JSON in the paired verified bundle's
  DSSE payload rather than from `verificationResult.statement`'s parsed
  protobuf/protojson view. The signed subject must bind the snapshotted package
  artifact and the signed predicate must exactly equal the downloaded canonical
  SPDX 3.0.1 document under lossless decimal JSON semantics.
- Protected-main signing now re-runs strict package-evidence admission after
  downloading the exact-head bundle and before the first attestation action, so
  corrupted, mixed, or download-drifted wheel/source/SPDX/checksum evidence
  cannot be converted into newly valid signed release evidence.
- Protected-main attestation verification now snapshots each release artifact
  before GitHub lookup and requires both the provenance and SPDX signed DSSE
  statements to carry that exact SHA-256 subject digest. SPDX predicate identity
  is evaluated only inside subject-matched signed statements, preventing
  provenance and SBOM evidence for different package bytes from being spliced.
- Data-management framework references now require a structural lowercase
  `https://` official locator even when JSON Schema `format` is annotation-only,
  and assessment profiles/results carry an exact semantic `profile_version` so
  historical score meaning cannot drift behind a stable profile code.
- Data-management assessment semantic validation now rejects same-tenant
  provenance evidence whose authority differs from the assessment-result
  authority, preventing another product authority from being relabeled as
  authoritative Data/AI assessment evidence.

### Added

- Source-bound release provenance through
  `cwl-context-release-source-manifest`, which strictly binds one verified
  wheel/source/SPDX package snapshot to protected `main`, the exact source SHA,
  repository and signer workflow, then requires the manifest itself to be
  attested and independently verified before its source fields are treated as
  release provenance. Duplicate/non-standard/oversized JSON fails closed, and
  the manifest remains evidence rather than application or domain authority.
- Dedicated exact-head release-package reproducibility acceptance that builds
  wheel and source distribution from two independent clean checkouts with a
  shared commit-derived `SOURCE_DATE_EPOCH`, rejects artifact-name or byte drift
  and symlink/path substitution, and retains SHA-256 evidence under the exact
  workflow commit identity.
- Framework-neutral `data-management-framework.schema.json` for relating
  CWL-authored capability, evidence, and assessment identifiers to external
  data-management framework references while reusing canonical authority,
  truth-status, and provenance grammar and keeping licensed framework content
  outside the public package.
- Framework-neutral `data-management-assessment.schema.json` plus packaged
  positive contract/result fixtures for exact 0..10000 basis-point scores,
  readiness/missing-evidence consistency, canonical tenant/subject identity,
  knowledge-cutoff and recorded-time evidence, truth status, provenance, and
  append-only supersession references without embedding publisher scoring rules.
- Portable `data-management-assessment-semantics.v1.json` conformance vectors
  for assessment authority ownership, tenant isolation, provenance-authority
  isolation, dimension identity, temporal ordering, and same-authority
  supersession; the installed reference runner and wheel smoke execute the same
  vectors delivered to consumers.
- Canonical tenant-scoped producer authority URI contract.
- Canonical UUIDv7-backed CWL asset URI contract.
- Truth-status vocabulary separating authoritative, observed, inferred, and
  proposed assertions.
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
  exact JSON integer exchange, and data-management assessment cross-field
  invariants; installed-package smoke tests execute the same vectors consumers
  receive.
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
- Composite `cwl-context-release-admit` command and
  `evaluate_packaged_contract_release_admission()` API that require executable
  semantic conformance, exact approved semantic-profile identity, and exact
  approved complete-resource identity together while leaving protected-release
  policy, artifact provenance, independent approval, and runtime authorization
  as separate owning gates.
- Buyer-executable `cwl-context-package-evidence-verify` command and
  `verify_package_evidence_directory()` API that require the workflow's exact
  same-version wheel/source/SPDX checksum set, reject malformed or escaping
  checksum names, refuse symlinked required evidence, recalculate every SHA-256
  digest, and require exactly one SPDX 3.0.1 `cwl-context-contracts` package
  whose `software_packageVersion` equals the wheel/source release version without
  promoting checksum equality to artifact provenance or release authority.
- Composite `cwl-context-release-evidence-admit` command and
  `evaluate_release_evidence_admission()` API that combine installed semantic
  and complete-resource admission with downloaded package-evidence verification
  and fail closed unless the verified wheel/source distribution version equals
  the installed approved distribution version, preventing coherent evidence
  from different releases from being spliced into one positive decision while
  leaving protected-main provenance, attestation, independent review, release
  authorization, and runtime authorization to their owning gates.
- Protected-main supply-chain admission now signs the one canonical SPDX 3.0.1
  JSON-LD through explicit in-toto `https://spdx.dev/Document/v3` custom-predicate
  mode, avoiding pinned `actions/attest` v4.2.2's SPDX-2 field-based automatic
  detector; it immediately verifies wheel/source SLSA and SPDX attestations
  against exact repository/ref/source/signer/OIDC/hosted-runner identity and
  retains machine-readable verifier results under the exact source SHA.
- ADR 0015 documents the protected-release attestation admission boundary,
  including downloaded-bundle re-admission, exact signed-DSSE subject/predicate
  identity, mutable-path rejection, and the explicit separation between
  deterministic evidence consistency and release authority.
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
