# Standard Traceability

| Product decision | External basis | Contract evidence |
|---|---|---|
| UUIDv7 event, asset, and assertion identity | Peabody et al. (2024, RFC 9562 §5.7) | URI parser, event validator, assertion schema |
| Producer `source` plus unique `id` | Cloud Native Computing Foundation (2022) | authority URI and envelope tests |
| Structured service event | Cloud Native Computing Foundation (2022) | envelope class and event schema |
| Absolute `dataschema` plus same-tenant event identity semantics | Cloud Native Computing Foundation (2022); JSON Schema (2022b, §7.2) | envelope round-trip/negative tests and packaged `cloudevent-semantics.v1.json` vectors covering absolute URI, source/subject tenant agreement, and `tenantid` agreement under default format-annotation semantics |
| CWL Timestamp Profile v1: RFC 3339-derived syntax, semantic calendar/clock/offset validation, leap seconds excluded | Klyne and Newman (2002); JSON Schema (2022b, §7.2) | ADR 0007, `parse_cwl_timestamp`, formatter round-trip/sub-minute-offset regressions, default-format-annotation regression, packaged `cwl-timestamp-profile.v1.json` vectors, interval mapping tests, installed-package smoke |
| Exact interoperable JSON integer boundary | Bray (2017, RFC 8259 §6) | event JSON validator, nested boundary regressions, packaged `cwl-json-interoperability.v1.json` vectors, installed-package smoke |
| Separate valid/system time | Jensen and Snodgrass (1996); Snodgrass (1995) | interval class, mapping, and reconstruction tests |
| Subject-predicate-object assertion | Cyganiak et al. (2014) | `ContextAssertion`, assertion schema, packaged `context-assertion-semantics.v1.json` cross-field negative vectors |
| Provenance reference model | Lebo et al. (2013); Moreau and Missier (2013) | provenance-reference schema and mapping; same-tenant semantic conformance vector |
| Multilevel / multi-membership affiliation | Diez-Roux (1998) | `ContextMembership`, unique memberships, packaged duplicate/foreign-context semantic vectors, consumer scenario tests |
| Provider-neutral message component | AsyncAPI Initiative (2026) | packaged components-only AsyncAPI resource; no servers, channels, operations, or broker topology |
| Schema dialect | JSON Schema (2022a, Draft 2020-12) | packaged `$schema` declarations and AsyncAPI payload `schemaFormat`; semantic profiles explicitly cover invariants structural JSON Schema does not enforce |
