# Security Policy

## Supported versions

Security fixes are applied to the latest released minor version and the current
`main` branch.

## Security invariants

- Event extensions may contain opaque identifiers, never credentials or raw
  personal data.
- Canonical URI parsing is fail-closed and rejects encoded delimiters,
  whitespace, non-UUIDv7 identifiers, and unknown authorities at consumer
  policy boundaries.
- Provenance digests are lowercase SHA-256 values. A digest proves byte
  identity, not trustworthiness or authorization.
- Schema validation does not authorize an event. Consumers must still verify
  issuer, tenant, purpose, and signature according to their own policy.

Report vulnerabilities privately to the organization maintainers rather than
opening a public issue.
