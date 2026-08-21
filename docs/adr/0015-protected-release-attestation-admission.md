# ADR 0015: Protected release attestation admission

- Status: Proposed — implemented on active PR #19, not yet protected-main shipped truth
- Date: 2026-08-21
- Decision owners: Context Graph Contracts maintainers

## Context

The contract package is intended to publish one canonical SPDX 3.0.1 SBOM together with wheel and source-distribution evidence. A protected-main release must not sign bytes merely because they were downloaded from an earlier workflow job, and a later verification pass must not accept provenance for one artifact byte sequence together with an SPDX statement for another.

GitHub CLI exposes each successfully verified attestation as a parsed in-toto statement under `verificationResult.statement`. The in-toto Statement v1 specification binds an attestation to its `subject` resources, and each subject is required to carry a digest. Therefore the subject digest is the correct portable boundary for proving that multiple verified statements refer to the same package bytes. The custom SPDX predicate remains separately bound to the retained canonical SPDX document.

## Decision

For a protected `main` release candidate:

1. Re-run the repository's strict package-evidence admission on the downloaded bundle before the first signing action. The downloaded wheel, source distribution, SPDX 3.0.1 document, and `SHA256SUMS` must still form the exact coherent evidence set produced by the package job.
2. Create SLSA provenance and SPDX 3 attestations only after that admission succeeds. SPDX 3 uses the explicit `https://spdx.dev/Document/v3` predicate boundary rather than an SPDX 2 compatibility downgrade.
3. Before querying GitHub for attestations, snapshot each release artifact through a stable regular-file descriptor and compute its SHA-256 digest.
4. Require every accepted provenance or SPDX verification path to contain a verified in-toto statement whose `subject` includes that exact SHA-256 digest. An artifact replacement between the provenance and SPDX checks therefore fails closed instead of allowing evidence splicing.
5. For the SPDX assertion, require the subject-matched statement's parsed predicate to equal the pre-verification canonical SPDX 3.0.1 snapshot by deterministic parsed-value SHA-256 identity.
6. Apply repository, protected source ref, exact source digest, signer workflow/digest, GitHub Actions OIDC issuer, and hosted-runner policy independently through `gh attestation verify`.
7. Evaluate the exact JSON bytes emitted by the successful verifier process before retaining them. Retained files are audit evidence, not a second mutable input to the admission decision.

This decision supplies deterministic artifact/provenance consistency only. It does not create a qualifying human approval, make an unprotected branch release-eligible, authorize publication, or replace downstream independent verification.

## Rejected alternatives

- **Sign immediately after artifact download.** Rejected because a corrupted, mixed, or drifted downloaded bundle could be converted into newly valid signed evidence without rechecking the repository's own checksum/SPDX admission.
- **Check only source repository and signer identity.** Rejected because those properties do not prove that separately verified provenance and SPDX statements bind the same package bytes.
- **Check only the SPDX predicate type.** Rejected because predicate type does not prove identity with the retained canonical SPDX document.
- **Downgrade the canonical SBOM to SPDX 2.x for convenience-mode parser compatibility.** Rejected because the repository's accepted evidence model is SPDX 3.0.1 and `actions/attest` supports explicit custom predicates.
- **Trust retained verification-result pathnames as the admission input.** Rejected because mutable pathnames permit replacement after the verifier process writes its output.

## Verification evidence

Executable acceptance lives in:

- `tests/test_workflow_integration_branches.py`, which requires downloaded package evidence to be re-admitted before the first protected-main attestation action;
- `tests/test_release_attestation_verifier_script.py`, including package-shape, protected-ref, SPDX predicate-drift, mutable-SBOM, verification-output replacement, and cross-attestation artifact-replacement regressions;
- `scripts/verify_release_attestations.sh`, which snapshots canonical SPDX and artifact identity before verification; and
- `scripts/verify_attestation_output.py`, which requires the verified statement subject and, for SPDX, the subject-matched predicate to bind those snapshots before retaining the exact verifier output.

Operational proof is intentionally deferred until the same reviewed implementation runs successfully on one exact integrated protected `main` SHA with all repository and governance gates satisfied together.

## References

See `docs/doctoring/REFERENCES.md` for the GitHub CLI artifact-attestation documentation, in-toto Statement and DigestSet specifications, SPDX 3.0.1, SLSA, and FIPS 180-4 references used by this decision.
