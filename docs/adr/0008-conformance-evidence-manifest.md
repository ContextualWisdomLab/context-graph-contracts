# ADR 0008: Bind semantic conformance evidence to exact packaged bytes

- Status: Accepted
- Date: 2026-08-17

## Context

The installed conformance runner proves how the reference SDK behaves against the semantic vectors present in an installation. A passing case count alone does not identify the exact bytes of those vectors. Two artifacts could therefore report the same profile names and passing case counts while carrying byte-different profile resources.

Context Graph Contracts is the provider-neutral interoperability boundary, so release and consumer evidence needs to distinguish **which semantic vectors ran** from **whether those vectors passed**. The evidence mechanism must remain contract-local and deterministic; it must not invent a registry, signing authority, trust service, or runtime policy engine.

## Decision

Publish an artifact-local conformance evidence manifest that:

1. enumerates every packaged semantic conformance profile in the package's stable profile-name order;
2. computes SHA-256 over the exact packaged byte sequence for each profile;
3. exposes the same evidence through a Python API and the `cwl-context-conformance-manifest` command;
4. rejects requests to hash unpublished profile names rather than fabricating evidence;
5. keeps semantic execution (`cwl-context-conformance`) separate from byte-identity evidence, so operators can retain both records together.

SHA-256 is the SHA-2 256-bit hash function specified by NIST FIPS 180-4. The manifest uses it only to identify exact resource bytes and detect change. A digest is **not** a signature, authorization decision, trust judgment, package-provenance claim, or proof that another implementation is conformant. Package hashes, SBOMs, protected-main attestations, reviewer policy, and consumer-side semantic execution remain independent gates.

## Consequences

- Any byte change to a packaged semantic profile changes its manifest digest even when the profile file name is unchanged.
- Buyers and release automation can archive the manifest next to the semantic conformance report and package/artifact hashes, making the executed vector set independently distinguishable.
- The manifest is reproducible from the installed package without network access or another CWL service.
- A self-generated digest does not establish trust in the artifact. Trust continues to come from the surrounding protected build/review/provenance controls.
- This repository remains contract-only: it does not persist manifests, verify organizational policy, or own consumer runtime state.

## Verification

Executable evidence is provided by `tests/test_conformance_manifest.py`, including exact `importlib.resources` byte hashing, unknown-profile rejection, deterministic manifest structure, and console-script metadata binding. The package workflow must still build and smoke-install wheel/sdist artifacts, while supply-chain evidence binds those distributions to exact-head package hashes and SBOM output.

## References

National Institute of Standards and Technology. (2015). *Secure Hash Standard (SHS)* (FIPS PUB 180-4). U.S. Department of Commerce. https://doi.org/10.6028/NIST.FIPS.180-4
