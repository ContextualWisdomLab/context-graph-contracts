"""Hostile-input regressions for approved conformance-manifest verification."""

from __future__ import annotations

import json

import cwl_context_contracts.conformance_manifest_verifier as verifier_module


def test_verifier_cli_rejects_excessive_json_nesting_without_traceback(
    tmp_path, capsys
) -> None:
    """Excessive nesting fails closed instead of escaping as RecursionError."""
    approved_path = tmp_path / "deeply-nested.json"
    nesting_depth = 10_000
    approved_path.write_text(
        "[" * nesting_depth + "0" + "]" * nesting_depth,
        encoding="utf-8",
    )

    exit_code = verifier_module.main([str(approved_path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["verified"] is False
    assert payload["error"] == "approved_manifest_invalid_json"
