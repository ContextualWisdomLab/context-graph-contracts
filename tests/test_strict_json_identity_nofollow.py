"""Require release evidence reads and writes to preserve no-follow semantics."""

from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

import pytest

_SCRIPT_PATH = Path("scripts/strict_json_identity.py")
_VERIFIER_SCRIPT_PATH = Path("scripts/verify_attestation_output.py")


def _load_script() -> dict[str, Any]:
    """Load the release-evidence helper without requiring scripts to be a package."""
    return runpy.run_path(str(_SCRIPT_PATH), run_name="strict_json_identity_under_test")


def _load_verifier_script(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Load the verifier with its sibling helper import available."""
    monkeypatch.syspath_prepend(str(_VERIFIER_SCRIPT_PATH.parent.resolve()))
    return runpy.run_path(
        str(_VERIFIER_SCRIPT_PATH),
        run_name="verify_attestation_output_under_test",
    )


def test_stable_json_reader_fails_closed_without_o_nofollow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Never silently downgrade a release-evidence read to symlink-following I/O."""
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text('{"name":"cwl-context-contracts"}', encoding="utf-8")
    module = _load_script()
    script_os = module["os"]
    monkeypatch.delattr(script_os, "O_NOFOLLOW", raising=False)

    with pytest.raises(OSError, match="platform lacks O_NOFOLLOW"):
        module["read_stable_regular_file"](
            evidence_path,
            label="downloaded SPDX evidence",
        )


def test_verification_writer_fails_closed_without_o_nofollow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Never retain verification evidence through a symlink-following fallback."""
    output_path = tmp_path / "verified.json"
    module = _load_verifier_script(monkeypatch)
    script_os = module["os"]
    monkeypatch.delattr(script_os, "O_NOFOLLOW", raising=False)

    with pytest.raises(OSError, match="platform lacks O_NOFOLLOW"):
        module["_write_exclusive_regular_file"](output_path, b"[]")

    assert not output_path.exists()
