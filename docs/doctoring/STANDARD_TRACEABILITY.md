# Standard Traceability

| Product decision | External basis | Contract evidence |
|---|---|---|
| UUIDv7 event, asset, and assertion identity | Peabody et al. (2024, RFC 9562 §5.7) | URI parser, event validator, assertion schema |
| Producer `source` plus unique `id` | Cloud Native Computing Foundation (2022) | authority URI and envelope tests |
| Structured service event | Cloud Native Computing Foundation (2022) | envelope class and event schema |
| Core `dataschema` handling | Cloud Native Computing Foundation (2022) | envelope round-trip and negative tests |
| RFC 3339 timestamp syntax and semantic validity | Klyne and Newman (2002); JSON Schema (2022b, §7.2) | shared parser, default-format-annotation regression, packaged `rfc3339-timestamp-profile.v1.json` vectors, interval mapping tests |
| Separate valid/system time | Jensen and Snodgrass (1996); Snodgrass (1995) | interval class, mapping, and reconstruction tests |
| Subject-predicate-object assertion | Cyganiak et al. (2014) | `ContextAssertion` and assertion schema |
| Provenance reference model | Lebo et al. (2013); Moreau and Missier (2013) | provenance-reference schema and mapping |
| Multilevel / multi-membership affiliation | Diez-Roux (1998) | `ContextMembership`, unique memberships, consumer scenario tests |
| Provider-neutral message component | AsyncAPI Initiative (2026) | packaged components-only AsyncAPI resource; no servers, channels, operations, or broker topology |
| Schema dialect | JSON Schema (2022a, Draft 2020-12) | packaged `$schema` declarations and AsyncAPI payload `schemaFormat` |
