# Test Strategy

- Unit tests exercise every validation branch in the Python reference package.
- Structured-event tests cover tenant mismatches, type confusion, non-finite
  numbers, non-string JSON keys, Python-only values, cycles, and excessive
  nesting.
- JSON Schema tests validate all schemas against Draft 2020-12.
- Positive and negative fixtures are packaged as executable conformance
  evidence.
- The CI matrix covers Python 3.11-3.13.
- Statement and branch coverage must both remain 100%.
- Package smoke tests install the built wheel outside the source tree.

Future language SDKs must consume the same fixture corpus and produce byte-wise
compatible structured events after canonical serialization.
