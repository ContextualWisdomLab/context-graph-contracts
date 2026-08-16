# Contributing

This repository publishes interoperability contracts. Keep changes
backward-compatible unless you introduce a new schema identifier and a major
version. Do not add a catalog, graph store, workflow engine, or user
interface here.

## Local development

The reference package is tested on Python 3.11, 3.12, 3.13, and 3.14 and has
no runtime third-party dependencies. Development extras provide pytest,
coverage, jsonschema, and Ruff. The supported test matrix is checked against
project metadata so this page cannot silently drift from executable evidence.

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
