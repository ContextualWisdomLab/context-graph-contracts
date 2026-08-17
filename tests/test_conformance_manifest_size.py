"""Resource-bound acceptance for approved conformance-manifest input."""

from __future__ import annotations

import json

import cwl_context_contracts.conformance_manifest_verifier as verifier_module


def test_verifier_cli_rejects_oversized_manifest_before_json_parsing(
    tmp_path, capsys
) -> None:
    """Hostile approved-manifest files cannot force an unbounded in-memory read."""
    approved_path = tmp_path / "oversized.json"
    approved_path.write_bytes(b" " * 1_048_577)

    exit_code = verifier_module.main([str(approved_path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["verified"] is False
    assert payload["error"] == "approved_manifest_too_large"
    assert payload["next_action"] == (
        "provide a readable approved conformance manifest JSON object"
    )
