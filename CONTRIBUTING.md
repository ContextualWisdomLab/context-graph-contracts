# Contributing

This repository publishes interoperability contracts. Keep changes
backward-compatible unless you introduce a new schema identifier and a major
version. Do not add a catalog, graph store, workflow engine, or user
interface here.

## Local development

The reference package targets Python 3.11–3.13 and has no runtime third-party
dependencies. Development extras provide pytest, coverage, jsonschema, and
Ruff.

```bash
uv sync --extra dev
uv run --extra dev python -m coverage run -m pytest -q
uv run --extra dev python -m coverage report
```

Production statement and branch coverage must remain 100%. See
`docs/TEST_STRATEGY.md` for the fixture and CI expectations.

## Documentation

- Product architecture: `docs/ARCHITECTURE.md`
- Accepted decisions: `docs/adr/`
- Cited standards: `docs/doctoring/REFERENCES.md`
