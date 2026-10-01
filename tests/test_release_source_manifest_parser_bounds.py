"""Parser-boundary regressions for release-source snapshot input."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwl_context_contracts import release_source_manifest as manifest_module

_REPOSITORY = "ContextualWisdomLab/context-graph-contracts"
_SOURCE_REF = "refs/heads/main"
_SOURCE_SHA = "0123456789abcdef0123456789abcdef01234567"
_SIGNER = f"{_REPOSITORY}/.github/workflows/supply-chain.yml"


def _cli(path: Path) -> int:
    """Invoke the release-source CLI through its exact authorized source identity."""
    return manifest_module.main(
        [
            str(path),
            "--source-repository",
            _REPOSITORY,
            "--source-ref",
            _SOURCE_REF,
            "--source-sha",
            _SOURCE_SHA,
            "--signer-workflow",
            _SIGNER,
        ]
    )


def test_utf16_json_snapshot_is_rejected_before_contract_validation(
    tmp_path: Path,
    capsys,
) -> None:
    """Release evidence is a UTF-8 JSON contract, not auto-detected JSON text."""
    path = tmp_path / "utf16.json"
    path.write_bytes("{}".encode("utf-16"))

    exit_code = _cli(path)
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["error"] == "package_snapshot_invalid"


def test_deeply_nested_json_is_rejected_before_recursive_decode(
    tmp_path: Path,
    capsys,
) -> None:
    """Untrusted snapshots cannot force decoder recursion beyond the input contract."""
    path = tmp_path / "deep.json"
    path.write_text("[" * 65 + "0" + "]" * 65, encoding="utf-8")

    exit_code = _cli(path)
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["error"] == "package_snapshot_too_deep"


@pytest.mark.parametrize(
    "payload",
    [
        b'"[not nesting]"',
        b'{"value":"escaped quote \\\" [ still text ]"}',
    ],
)
def test_depth_scanner_ignores_brackets_inside_json_strings(
    tmp_path: Path,
    capsys,
    payload: bytes,
) -> None:
    """Depth defense must not reinterpret string contents as structural nesting."""
    path = tmp_path / "string.json"
    path.write_bytes(payload)

    exit_code = _cli(path)
    result = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert result["error"] == "package_snapshot_invalid"
