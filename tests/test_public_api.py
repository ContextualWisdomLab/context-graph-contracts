"""Public API and documentation tests."""

import inspect

import cwl_context_contracts


def test_public_symbols_have_docstrings_and_version() -> None:
    """All exported symbols are documented and versioned."""

    assert cwl_context_contracts.__version__ == "0.1.0"
    for name in cwl_context_contracts.__all__:
        assert inspect.getdoc(getattr(cwl_context_contracts, name)), name
