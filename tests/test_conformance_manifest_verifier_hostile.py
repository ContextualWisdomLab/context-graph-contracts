"""Hostile-input regressions for approved conformance-manifest verification."""

from __future__ import annotations

import json
from typing import Any

import cwl_context_contracts.conformance_manifest_verifier as verifier_module


def test_verifier_cli_rejects_parser_recursion_without_traceback(
    tmp_path, capsys, monkeypatch
) -> None:
    """A parser recursion limit fails closed instead of escaping as RecursionError."""
    approved_path = tmp_path / "approved.json"
    approved_path.write_text("{}", encoding="utf-8")
    parse_output = json.loads

    def recursive_parse(*args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        raise RecursionError("manifest nesting exceeded parser recursion limit")

    monkeypatch.setattr(verifier_module.json, "loads", recursive_parse)

    exit_code = verifier_module.main([str(approved_path)])

    payload = parse_output(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["verified"] is False
    assert payload["error"] == "approved_manifest_invalid_json"
