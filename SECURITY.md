# Security Policy

## Supported versions

Security fixes are applied to the latest released minor version and the current
default branch.

## Security invariants

- Event extensions may contain opaque identifiers, never credentials or raw
  personal data.
- Canonical URI parsing is fail-closed and rejects encoded delimiters,
  whitespace, non-UUIDv7 identifiers, and unknown authorities at consumer
  policy boundaries.
- Event producer and subject references remain inside one tenant boundary; a
  redundant `tenantid` extension cannot contradict the producer authority.
- Structured-event core attributes are never silently coerced from non-string
  values. Event data rejects non-finite numbers, non-string keys, Python-only
  objects, cyclic containers, and nesting deeper than 64 levels.
- Provenance digests are lowercase SHA-256 values. A digest proves byte
  identity, not trustworthiness or authorization.
- Schema validation does not authorize an event. Consumers must still verify
  issuer, tenant, purpose, and signature according to their own policy.
- Interchange metadata uses opaque asset URIs. Do not put credentials, DSNs,
  raw personal data, or source payloads in envelopes or assertion bodies.
- Masking personal data in a system of record is not a substitute for access
  control, purpose limitation, and audit. This contract layer therefore does
  not mask producer data; it keeps personal data in the owning product and
  exchanges references. That is the SOC 2 CC6 / CSAP-aligned alternative to
  envelope-level masking that would break downstream work.

Report vulnerabilities privately to the organization maintainers rather than
opening a public issue.
