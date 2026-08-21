#!/usr/bin/env python3
"""Verify GitHub attestation JSON from stdin and retain the exact verified bytes."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

_MAX_JSON_BYTES = 16 * 1024 * 1024


class DuplicateJsonMember(ValueError):
    """Signal that an input JSON object repeats a member name."""


def _reject_duplicate_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object only when every member name is unique."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonMember(f"duplicate JSON member: {key}")
        result[key] = value
    return result


def _reject_nonstandard_constant(value: str) -> None:
    """Reject NaN and Infinity extensions because they are not valid JSON."""
    raise ValueError(f"non-standard JSON numeric constant: {value}")


def _read_bounded_stdin() -> bytes:
    """Read at most 16 MiB of attestation JSON plus one overflow sentinel byte."""
    data = sys.stdin.buffer.read(_MAX_JSON_BYTES + 1)
    if len(data) > _MAX_JSON_BYTES:
        raise ValueError("GitHub attestation verification JSON exceeds 16 MiB")
    return data


def _load_strict_json(data: bytes) -> Any:
    """Parse UTF-8 JSON without duplicate members or non-standard numbers."""
    return json.loads(
        data.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_members,
        parse_constant=_reject_nonstandard_constant,
    )


def _normalized_json(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON used only for parsed-value identity."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _require_nonempty_verification_array(verification: Any) -> list[Any]:
    """Require the documented non-empty array shape emitted by ``gh attestation``."""
    if not isinstance(verification, list) or not verification:
        raise ValueError("gh attestation verification must return a non-empty JSON array")
    return verification


def _require_matching_spdx_predicate(
    verification: list[Any], expected_digest: str
) -> None:
    """Require one signed predicate whose parsed-value digest matches the SBOM."""
    for candidate in verification:
        if not isinstance(candidate, dict):
            continue
        result = candidate.get("verificationResult")
        if not isinstance(result, dict):
            continue
        statement = result.get("statement")
        if not isinstance(statement, dict) or "predicate" not in statement:
            continue
        candidate_digest = hashlib.sha256(
            _normalized_json(statement["predicate"])
        ).hexdigest()
        if candidate_digest == expected_digest:
            return
    raise ValueError("attested SPDX predicate does not match downloaded package SBOM")


def _write_exclusive_regular_file(path: Path, data: bytes) -> None:
    """Retain exactly the verified bytes without following or replacing a path."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        opened_stat = os.fstat(descriptor)
        if not stat.S_ISREG(opened_stat.st_mode):
            raise ValueError(f"verification output is not a regular file: {path}")
        view = memoryview(data)
        written = 0
        while written < len(view):
            written += os.write(descriptor, view[written:])
        os.fsync(descriptor)
        path_stat = os.stat(path, follow_symlinks=False)
        if not stat.S_ISREG(path_stat.st_mode):
            raise ValueError(f"verification output path stopped being regular: {path}")
        if (opened_stat.st_dev, opened_stat.st_ino) != (
            path_stat.st_dev,
            path_stat.st_ino,
        ):
            raise ValueError(f"verification output path changed while being written: {path}")
    finally:
        os.close(descriptor)


def main(argv: list[str]) -> int:
    """Verify stdin and retain it only after all requested semantic checks pass."""
    if len(argv) not in {2, 3}:
        print(
            "usage: verify_attestation_output.py OUTPUT_PATH [EXPECTED_SBOM_DIGEST]",
            file=sys.stderr,
        )
        return 2

    output_path = Path(argv[1])
    expected_digest = argv[2] if len(argv) == 3 else None
    if expected_digest is not None and (
        len(expected_digest) != 64
        or any(character not in "0123456789abcdef" for character in expected_digest)
    ):
        print("expected SBOM digest must be lowercase SHA-256 hex", file=sys.stderr)
        return 1

    try:
        data = _read_bounded_stdin()
        verification = _require_nonempty_verification_array(_load_strict_json(data))
        if expected_digest is not None:
            _require_matching_spdx_predicate(verification, expected_digest)
        _write_exclusive_regular_file(output_path, data)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"unable to verify/retain attestation evidence strictly: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
