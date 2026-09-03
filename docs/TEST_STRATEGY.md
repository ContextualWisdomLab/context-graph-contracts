# Test Strategy

- Unit tests exercise every validation branch in the Python reference package.
- Structured-event tests cover tenant mismatches, type confusion, non-finite
  numbers, non-string JSON keys, Python-only values, cycles, and excessive
  nesting.
- Context Assertion transport-admission tests bind the executable consumer
  boundary to the AsyncAPI JSON structured-event media type, accept the
  case-insensitive CloudEvents media type and its UTF-8 `charset` form used by
  the HTTP structured binding, and reject wrong charsets, duplicate/unknown
  parameters, mismatched media types, CRLF injection, and non-string values.
- JSON Schema tests validate all schemas against Draft 2020-12.
- Positive and negative fixtures are packaged as executable conformance
  evidence.
- Data-management framework tests require publisher reference metadata to remain
  portable when a Draft 2020-12 implementation treats `format` as annotation:
  official framework locations must match the structural lowercase `https://`
  assertion, while missing-scheme, `http:`, `javascript:`, and `data:` references
  fail closed. This syntax gate does not authorize dereferencing; products that
  fetch an external reference retain their own SSRF/network-policy boundary.
- Data-management assessment tests separate structural schema acceptance from
  cross-field semantics. `validate_data_management_assessment_semantics()`
  requires the result ID to use the assessment object kind and declared owning
  authority, keeps primary/supersession references inside one tenant, requires
  provenance evidence to remain both tenant-local and under the assessment
  result's owning authority, rejects duplicate dimension codes, and requires the
  evidence knowledge cutoff not to follow system recording time. Supersession
  must reference a different assessment result under the same tenant and owning
  authority; prior evidence is never rewritten and one authority cannot
  supersede another authority's assessment history. The negative corpus includes
  same-tenant foreign-authority provenance so tenant equality cannot substitute
  for source-authority ownership. These invariants are also published in
  `data-management-assessment-semantics.v1.json`, so non-Python consumers can
  execute the same valid and invalid vectors instead of treating the reference
  SDK implementation as the contract.
- Timestamp tests deliberately run Draft 2020-12 without a format checker to
  prove that default `format` annotation cannot establish semantic validity,
  then execute the packaged provider-neutral CWL Timestamp Profile v1 vectors
  through the reference parser. Calendar-impossible dates, invalid clock
  values, invalid offsets, and leap-second lexical `:60` must fail this named
  profile even though RFC 3339 itself can represent leap seconds.
- Assertion tests use consumer-shaped cases: a LineageWeave inferred
  `derived_from` edge, an enterprise-architecture `proposed` `realized_by`
  edge, cross-classified analysis-run plus employment-group membership, and
  exclusive-end temporal reconstruction.
- Conformance evidence tests execute every packaged semantic profile through
  `cwl-context-conformance`, bind the exact installed distribution version and
  profile bytes with `cwl-context-conformance-manifest`, compare that evidence
  with an independently supplied approved manifest through
  `cwl-context-conformance-verify`, and require the composite
  `cwl-context-conformance-admit` gate to rerun semantics plus exact manifest
  verification before reporting admission.
- Complete-resource evidence tests require `cwl-context-bundle-manifest` and
  `build_packaged_contract_bundle_manifest()` to bind the installed
  distribution version to SHA-256 of every explicitly published AsyncAPI,
  JSON Schema, fixture, and semantic-profile byte sequence in stable
  category-prefixed resource-path order. The regression independently reads
  those packaged bytes rather than trusting the manifest under test.
- Complete-bundle verification tests compare independently approved full
  resource evidence through `cwl-context-bundle-verify` and
  `verify_packaged_contract_bundle_manifest()`. They require exact package
  identity, strict integer count semantics, unique resource paths, and exact
  missing/unexpected/digest-different resource mismatch identities.
- Full installed release-admission tests compose both existing evidence layers
  through `cwl-context-release-admit` and
  `evaluate_packaged_contract_release_admission()`. They require semantic
  execution plus exact approved semantic-profile and complete-resource identity,
  prove either approval layer can independently block admission, verify distinct
  exit `0`/`1`/`2` machine semantics, and preserve protected-release,
  provenance, independent-review, and runtime-authorization boundaries.
- Package-evidence tests independently verify the workflow-produced wheel,
  source distribution, SPDX 3.0.1 document, and `SHA256SUMS` set. Regressions
  cover artifact/version-set drift, digest drift, malformed checksum input,
  duplicate identities, traversal, symlink/path replacement, bounded metadata,
  duplicate/non-standard JSON, and exact installed-wheel command behavior.
- Complete release-evidence admission tests compose installed release admission
  with package-evidence verification through
  `cwl-context-release-evidence-admit` and
  `evaluate_release_evidence_admission()`. A coherent package bundle from a
  different distribution version must fail even when both component gates pass;
  tampered package bytes and approved contract drift fail independently. The
  command preserves distinct success, rejected-valid-input, and malformed-input
  exit semantics and never promotes deterministic consistency to provenance or
  release authority.
- Protected-main attestation workflow regressions require the canonical SPDX
  3.0.1 JSON-LD to be supplied to pinned `actions/attest` through explicit
  `https://spdx.dev/Document/v3` custom-predicate mode rather than its SPDX-2
  automatic detector. They require exact repository/ref/source-digest/signer
  identity, GitHub Actions OIDC issuer, hosted-runner policy, one wheel plus one
  source distribution, both SLSA and SPDX predicate verification, and
  machine-readable verification-result retention under the exact source SHA.
  The executable verifier additionally requires the downloaded canonical SPDX
  document to be a regular file, parses the retained document with strict
  bounded JSON semantics, and treats `gh attestation verify --format json` as a
  paired verified-bundle/result envelope: it requires `verificationResult` to
  exist, then decodes the exact base64 `attestation.bundle.dsseEnvelope.payload`,
  requires the in-toto payload type, and parses the signed statement itself with
  duplicate-safe exact-decimal semantics. Artifact subjects and the SPDX
  predicate are compared only from this signed DSSE statement, never from the
  convenience protobuf/protojson `verificationResult.statement` identity view.
  The large-decimal regression deliberately gives the signed payload
  `9007199254740993.0` while the parsed statement view is rounded to
  `9007199254740992`, proving that the rounded view cannot authorize admission.
  Missing/malformed bundle structure, invalid base64, wrong payload type,
  subject drift, predicate drift, mutable SBOM/output paths, and cross-check
  artifact replacement all fail closed. Predicate type alone is therefore
  insufficient evidence of SBOM identity. Pull-request tests prove the workflow
  contract only; operational attestation verification is not considered passing
  evidence until this same job executes successfully on an exact integrated
  protected `main` SHA.
- Verifier regressions fail closed on package-version drift, missing,
  unexpected, duplicate, malformed, or digest-different profile/resource
  evidence, type-confused counts, unreadable or invalid UTF-8/JSON input, and
  non-object manifests. Exact matches, drift, and invalid input have distinct
  machine-readable exit semantics.
- Composite-admission regressions prove semantic failure blocks admission even
  when the approved manifest matches, manifest drift blocks admission after a
  semantic pass, and hostile manifest input reuses the same bounded strict JSON
  parser rather than a second permissive path.
- The CI matrix covers Python 3.11-3.14 and verifies the committed lockfile.
- Statement and branch coverage must both remain 100%.
- Package smoke tests install the built wheel outside the source tree, verify
  schemas, fixtures, contracts, and semantic conformance profiles are present,
  then execute the installed conformance runner, semantic manifest generator,
  approved-manifest verifier, composite admission gate, admission receipt,
  complete contract-bundle manifest, approved full-bundle verifier, installed
  release-admission command, package-evidence verifier, and complete
  release-evidence admission command from an isolated wheel installation.

Future language SDKs must consume the same fixture and conformance-profile
corpus and produce byte-wise compatible structured events after canonical
serialization. A language SDK is not considered compatible merely because its
package name or version matches; it must preserve the same semantic vectors and
release-evidence comparison boundary.
