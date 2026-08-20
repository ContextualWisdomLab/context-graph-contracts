"""Regression for same-inode symlink replacement at the evidence-file boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from cwl_context_contracts import verify_package_evidence_directory


def _digest(payload: bytes) -> str:
    """Return one workflow-compatible SHA-256 digest."""
    return hashlib.sha256(payload).hexdigest()


def _valid_sbom() -> bytes:
    """Return one valid SPDX package document for release 0.1.0."""
    return json.dumps(
        {
            "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
            "@graph": [
                {"type": "CreationInfo", "specVersion": "3.0.1"},
                {
                    "type": "software_Package",
                    "name": "cwl-context-contracts",
                    "software_packageVersion": "0.1.0",
                },
            ],
        },
        sort_keys=True,
    ).encode()


def test_same_inode_symlink_swap_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A symlink replacement cannot pass merely by resolving to the checked inode."""
    artifacts = {
        "cwl_context_contracts-0.1.0-py3-none-any.whl": b"wheel",
        "cwl_context_contracts-0.1.0.tar.gz": b"sdist",
        "cwl-context-contracts.spdx.json": _valid_sbom(),
    }
    for name, payload in artifacts.items():
        (tmp_path / name).write_bytes(payload)
    (tmp_path / "SHA256SUMS").write_text(
        "".join(
            f"{_digest(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )

    target = tmp_path / "cwl-context-contracts.spdx.json"
    renamed_target = tmp_path / "checked-spdx-same-inode.json"
    original_open = Path.open
    swapped = False

    def replace_with_symlink_to_same_inode(
        path: Path,
        *args: object,
        **kwargs: object,
    ):
        nonlocal swapped
        if path == target and not swapped:
            swapped = True
            path.rename(renamed_target)
            path.symlink_to(renamed_target.name)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", replace_with_symlink_to_same_inode)

    report = verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == (
        "artifact_unsafe:cwl-context-contracts.spdx.json",
    )
