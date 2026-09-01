# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Changed

- PR #20 runner-image contract regression now satisfies the repository Ruff module/import contract; predecessor exact-head Python 3.11–3.14 lanes failed deterministically at `I001` because `tests/test_runner_image_contract.py` contained one excess blank line after its import. The repair removes only that formatting defect without changing the runner-policy assertion or weakening CI.
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
  artifact download and before attestation, then verifies the complete retained
  artifact directory again after signing so same-inode or path-replacement
  mutation cannot silently survive the release-evidence boundary.
- Protected-main package evidence now requires package bytes, SPDX identity,
  checksums, source commit identity, independently reproduced artifacts, and
  retained attestation verification output to remain mutually coherent before
  release admission can succeed.
