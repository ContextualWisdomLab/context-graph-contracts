# ADR 0015: Protected release attestation admission

- Status: Proposed — implemented on active PR #19, not yet protected-main shipped truth
- Date: 2026-08-21
- Decision owners: Context Graph Contracts maintainers

## Context

The contract package is intended to publish one canonical SPDX 3.0.1 SBOM together with wheel and source-distribution evidence. A protected-main release must not sign bytes merely because they were downloaded from an earlier workflow job, and a later verification pass must not accept provenance for one artifact byte sequence together with an SPDX statement for another.

`gh attestation verify --format json` exposes both the verified attestation bundle and a parsed `verificationResult.statement`. The latter is useful for inspection, but it is not a lossless semantic-identity boundary for arbitrary JSON predicates: the GitHub CLI delegates verification to sigstore-go, whose `VerificationResult` carries an in-toto protobuf `Statement` and marshals that statement through `protojson`. Generic predicate values are represented through protobuf's JSON value model, whose numeric representation is binary64. A distinct signed decimal value can therefore already have been rounded before the parsed statement is emitted. The verified result and its paired `attestation.bundle.dsseEnvelope.payload` refer to the same successfully verified bundle, while the DSSE payload contains the exact signed in-toto JSON bytes. Release admission must therefore derive subject and predicate identity from that signed DSSE payload, not from the lossy parsed statement view.

The in-toto Statement v1 specification binds an attestation to its `subject` resources, and each subject is required to carry a digest. Therefore the subject digest is the correct portable boundary for proving that multiple verified statements refer to the same package bytes. The custom SPDX predicate remains separately bound to the retained canonical SPDX document.

SLSA Build Provenance v1 also treats build external parameters as untrusted inputs that downstream consumers must verify. The pinned GitHub `actions/attest` implementation generates the GitHub Actions workflow build type `https://actions.github.io/buildtypes/workflow/v1` from OIDC claims, including the protected source ref, repository and workflow path, the resolved Git commit, and the builder workflow identity. Merely checking the predicate type `https://slsa.dev/provenance/v1` would therefore admit a signed but content-free or differently parameterized provenance predicate. Release admission must verify these policy-relevant signed predicate fields against the exact protected release context.

JSON evidence identity also has to preserve number meaning exactly. Parsing arbitrary JSON numbers through a binary floating-point intermediary can collapse distinct decimal literals—for example values immediately above the IEEE 754 exact-integer boundary—into one value before comparison. Release admission therefore decodes the verified bundle's signed DSSE payload, parses that payload with exact decimals, and uses an injective parsed-value encoding rather than binary-float normalization.

## Decision

For a protected `main` release candidate:

1. Re-run the repository's strict package-evidence admission on the downloaded bundle before the first signing action. The downloaded wheel, source distribution, SPDX 3.0.1 document, and `SHA256SUMS` must still form the exact coherent evidence set produced by the package job.
2. Create SLSA provenance and SPDX 3 attestations only after that admission succeeds. SPDX 3 uses the explicit `https://spdx.dev/Document/v3` predicate boundary rather than an SPDX 2 compatibility downgrade.
3. Before querying GitHub for attestations, snapshot each release artifact through a stable regular-file descriptor and compute its SHA-256 digest.
4. For every candidate emitted as successfully verified by `gh`, decode the paired bundle's base64 DSSE payload, require the in-toto payload type, parse the signed JSON strictly, and require the signed statement's `subject` to include the exact pre-verification artifact SHA-256 digest. An artifact replacement between the provenance and SPDX checks therefore fails closed instead of allowing evidence splicing.
5. For the SLSA provenance assertion, require the subject-matched signed DSSE statement to use the pinned GitHub Actions workflow build type and to bind the exact protected ref, repository URL, workflow path, resolved Git commit, and builder workflow identity emitted by the pinned `actions/attest` implementation. Reject missing or unexpected external parameters rather than accepting predicate-type-only provenance.
6. For the SPDX assertion, require the subject-matched **signed DSSE statement's** predicate to equal the pre-verification canonical SPDX 3.0.1 snapshot by deterministic parsed-value SHA-256 identity. Parse every JSON number losslessly as an exact decimal and encode the parsed JSON value injectively before hashing. Never use `verificationResult.statement.predicate` as the identity source, because its protobuf/protojson representation can already have rounded a distinct legal JSON number.
7. Apply repository, protected source ref, exact source digest, signer workflow/digest, GitHub Actions OIDC issuer, and hosted-runner policy independently through `gh attestation verify`. These certificate/source filters complement rather than replace signed SLSA predicate validation.
8. Evaluate the exact JSON bytes emitted by the successful verifier process before retaining them. Reject malformed/missing verified bundle structure, invalid base64, unexpected DSSE payload type, duplicate JSON members, non-standard numeric constants, malformed UTF-8/JSON, oversized evidence, subject drift, provenance build-identity drift, and predicate drift. Retained files are audit evidence, not a second mutable input to the admission decision.

This decision supplies deterministic artifact/provenance consistency only. It does not create a qualifying human approval, make an unprotected branch release-eligible, authorize publication, or replace downstream independent verification.

## Rejected alternatives

- **Sign immediately after artifact download.** Rejected because a corrupted, mixed, or drifted downloaded bundle could be converted into newly valid signed evidence without rechecking the repository's own checksum/SPDX admission.
- **Check only source repository and signer identity.** Rejected because those properties do not prove that separately verified provenance and SPDX statements bind the same package bytes or that the signed SLSA predicate describes the expected build invocation.
- **Check only the SLSA predicate type.** Rejected because a signed statement can carry the correct `predicateType` while omitting or changing the GitHub Actions build definition, external workflow parameters, resolved source commit, or builder identity that downstream SLSA consumers are expected to verify.
- **Check only the SPDX predicate type.** Rejected because predicate type does not prove identity with the retained canonical SPDX document.
- **Use `verificationResult.statement` as the semantic identity source.** Rejected because the GitHub CLI's parsed verification statement is materialized through an in-toto protobuf/protojson representation; generic JSON predicate numbers can be rounded before policy code receives that view. The paired signed DSSE payload is the lossless source of signed statement bytes.
- **Normalize evidence through ordinary binary floating point.** Rejected because distinct legal JSON decimal numbers can round to the same machine float and produce a false predicate-identity match.
- **Downgrade the canonical SBOM to SPDX 2.x for convenience-mode parser compatibility.** Rejected because the repository's accepted evidence model is SPDX 3.0.1 and `actions/attest` supports explicit custom predicates.
- **Trust retained verification-result pathnames as the admission input.** Rejected because mutable pathnames permit replacement after the verifier process writes its output.

## Verification evidence

Executable acceptance lives in:

- `tests/test_workflow_integration_branches.py`, which requires downloaded package evidence to be re-admitted before the first protected-main attestation action;
- `tests/test_provenance_attestation_policy.py`, which admits the exact pinned GitHub Actions SLSA build identity and rejects content-free provenance, wrong protected refs, wrong resolved commits, wrong builder workflows, and unexpected external parameters;
- `tests/test_release_attestation_verifier_script.py`, including package-shape, protected-ref, realistic GitHub Actions provenance, SPDX predicate-drift, mutable-SBOM, verification-output replacement, signed-bundle shape, and cross-attestation artifact-replacement regressions;
- `tests/test_release_attestation_numeric_identity.py`, which simulates a signed decimal above the binary64 exact-integer boundary together with a rounded `verificationResult.statement` view and proves admission follows the exact signed DSSE payload instead;
- `scripts/strict_json_identity.py`, which performs bounded strict JSON parsing and lossless semantic identity;
- `scripts/verify_release_attestations.sh`, which snapshots canonical SPDX and artifact identity before verification; and
- `scripts/verify_attestation_output.py`, which decodes the verified bundle's signed DSSE payload and requires its statement subject, SLSA build identity, and, for SPDX, its predicate to bind the protected release context before retaining the exact verifier output.

Operational proof is intentionally deferred until the same reviewed implementation runs successfully on one exact integrated protected `main` SHA with all repository and governance gates satisfied together.

## References

See `docs/doctoring/REFERENCES.md` for SLSA v1.2, the exact pinned GitHub `actions/attest` release and `@actions/attest` provenance implementation, GitHub CLI artifact-attestation documentation and implementation, sigstore-go verification-result implementation, Sigstore DSSE protobuf specification, in-toto Statement and DigestSet specifications, SPDX 3.0.1, RFC 8259, and FIPS 180-4 references used by this decision.
