"""Regressions for path replacement at the package-evidence file boundary."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import BinaryIO

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


def _write_valid_bundle(tmp_path: Path) -> Path:
    """Write one internally coherent package-evidence directory and return its SBOM."""
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
    return tmp_path / "cwl-context-contracts.spdx.json"


def _assert_sbom_unsafe(tmp_path: Path) -> None:
    """Require the public verifier to reject the SBOM as unsafe evidence."""
    report = verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == (
        "artifact_unsafe:cwl-context-contracts.spdx.json",
    )


def test_same_inode_symlink_swap_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A symlink replacement cannot pass merely by resolving to the checked inode."""
    target = _write_valid_bundle(tmp_path)
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

    _assert_sbom_unsafe(tmp_path)


def test_same_inode_content_rewrite_during_read_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An in-place rewrite cannot leave a pre-rewrite snapshot accepted as stable."""
    target = _write_valid_bundle(tmp_path)
    original_inode = target.stat().st_ino
    original_open = Path.open
    replacement = _valid_sbom().replace(b"0.1.0", b"9.9.9")
    mutated = False

    class MutatingHandle:
        """Delegate binary I/O while rewriting the same inode after its first read."""

        def __init__(self, handle: BinaryIO) -> None:
            self._handle = handle

        def fileno(self) -> int:
            return self._handle.fileno()

        def read(self, *args: object) -> bytes:
            nonlocal mutated
            data = self._handle.read(*args)
            if data and not mutated:
                descriptor = os.open(target, os.O_WRONLY | os.O_TRUNC)
                try:
                    os.write(descriptor, replacement)
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
                mutated = True
            return data

        def close(self) -> None:
            self._handle.close()

        def __enter__(self) -> MutatingHandle:
            return self

        def __exit__(self, *args: object) -> None:
            self.close()

    def mutate_after_read(
        path: Path,
        *args: object,
        **kwargs: object,
    ):
        handle = original_open(path, *args, **kwargs)
        if path == target:
            return MutatingHandle(handle)
        return handle

    monkeypatch.setattr(Path, "open", mutate_after_read)

    _assert_sbom_unsafe(tmp_path)
    assert mutated
    assert target.stat().st_ino == original_inode


def test_post_open_path_disappearance_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Losing the final path after open cannot leave an accepted file descriptor."""
    target = _write_valid_bundle(tmp_path)
    original_stat = Path.stat
    nofollow_stat_count = 0

    def disappear_on_post_open_stat(
        path: Path,
        *args: object,
        **kwargs: object,
    ):
        nonlocal nofollow_stat_count
        if path == target and kwargs.get("follow_symlinks") is False:
            nofollow_stat_count += 1
            if nofollow_stat_count == 2:
                raise FileNotFoundError("evidence path disappeared after open")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", disappear_on_post_open_stat)

    _assert_sbom_unsafe(tmp_path)


def test_post_read_path_disappearance_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Losing the final path after bytes are read must invalidate that snapshot."""
    target = _write_valid_bundle(tmp_path)
    original_stat = Path.stat
    nofollow_stat_count = 0

    def disappear_on_post_read_stat(
        path: Path,
        *args: object,
        **kwargs: object,
    ):
        nonlocal nofollow_stat_count
        if path == target and kwargs.get("follow_symlinks") is False:
            nofollow_stat_count += 1
            if nofollow_stat_count == 3:
                raise FileNotFoundError("evidence path disappeared after read")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", disappear_on_post_read_stat)

    _assert_sbom_unsafe(tmp_path)
    assert nofollow_stat_count == 3


def test_post_open_regular_inode_replacement_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A different regular inode at the final path cannot inherit opened identity."""
    target = _write_valid_bundle(tmp_path)
    replacement = tmp_path / "replacement-spdx.json"
    replacement.write_bytes(_valid_sbom())
    replacement_stat = replacement.stat(follow_symlinks=False)
    original_stat = Path.stat
    nofollow_stat_count = 0

    def report_replaced_regular_inode(
        path: Path,
        *args: object,
        **kwargs: object,
    ):
        nonlocal nofollow_stat_count
        if path == target and kwargs.get("follow_symlinks") is False:
            nofollow_stat_count += 1
            if nofollow_stat_count == 2:
                return replacement_stat
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", report_replaced_regular_inode)

    _assert_sbom_unsafe(tmp_path)
