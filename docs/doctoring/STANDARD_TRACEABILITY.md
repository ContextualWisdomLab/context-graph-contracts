# Standard Traceability

| Product decision | External basis | Contract evidence |
|---|---|---|
| UUIDv7 event and asset identity | RFC 9562 §5.7 | URI parser, event validator, and schemas |
| Producer `source` plus unique `id` | CloudEvents 1.0.2 | authority URI and envelope tests |
| Structured service event | CloudEvents 1.0.2 | envelope class and event schema |
| Core `dataschema` handling | CloudEvents 1.0.2 | envelope round-trip and negative tests |
| Provenance reference model | W3C PROV-O | provenance-reference schema |
| Schema dialect | JSON Schema Draft 2020-12 | packaged `$schema` declarations |
| Separate valid/system time | Bitemporal product requirement | interval class and tests |
