#!/usr/bin/env python3
"""Verify GitHub attestation JSON from stdin and retain the exact verified bytes."""

from __future__ import annotations

import base64
import binascii
import os
import stat
import sys
from pathlib import Path
from typing import Any

from strict_json_identity import MAX_JSON_BYTES, load_strict_json, semantic_json_sha256

_IN_TOTO_PAYLOAD_TYPE = "application/vnd.in-toto+json"


def _read_bounded_stdin() -> bytes:
    """Read at most 16 MiB of attestation JSON plus one overflow sentinel byte."""
    data = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
    if len(data) > MAX_JSON_BYTES:
        raise ValueError("GitHub attestation verification JSON exceeds 16 MiB")
    return data


def _require_nonempty_verification_array(verification: Any) -> list[Any]:
    """Require the documented non-empty array shape emitted by ``gh attestation``."""
    if not isinstance(verification, list) or not verification:
        message = "gh attestation verification must return a non-empty JSON array"
        raise ValueError(message)
    return verification


def _signed_statement_from_verified_candidate(candidate: Any) -> dict[str, Any] | None:
    """Return the exact signed in-toto statement paired with one verified result."""
    if not isinstance(candidate, dict):
        return None
    result = candidate.get("verificationResult")
    if not isinstance(result, dict):
        return None
    if not isinstance(result.get("statement"), dict):
        raise ValueError("verified attestation is missing its parsed statement")

    attestation = candidate.get("attestation")
    if not isinstance(attestation, dict):
        raise ValueError("verified attestation is missing its signed bundle")
    bundle = attestation.get("bundle")
    if not isinstance(bundle, dict):
        raise ValueError("verified attestation is missing its signed bundle")
    envelope = bundle.get("dsseEnvelope")
    if not isinstance(envelope, dict):
        raise ValueError("verified attestation is missing its DSSE envelope")
    if envelope.get("payloadType") != _IN_TOTO_PAYLOAD_TYPE:
        raise ValueError("verified attestation has an unexpected DSSE payload type")

    encoded_payload = envelope.get("payload")
    if not isinstance(encoded_payload, str):
        raise ValueError("verified attestation is missing its signed DSSE payload")
    try:
        payload = base64.b64decode(encoded_payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("verified attestation has invalid base64 DSSE payload") from exc
    if len(payload) > MAX_JSON_BYTES:
        raise ValueError("signed DSSE statement exceeds 16 MiB")

    statement = load_strict_json(payload)
    if not isinstance(statement, dict):
        raise ValueError("signed DSSE payload must be an in-toto JSON object")
    return statement


def _matching_artifact_statements(
    verification: list[Any], expected_artifact_digest: str
) -> list[dict[str, Any]]:
    """Return signed statements whose subject names the exact artifact digest."""
    statements: list[dict[str, Any]] = []
    for candidate in verification:
        statement = _signed_statement_from_verified_candidate(candidate)
        if statement is None:
            continue
        subjects = statement.get("subject")
        if not isinstance(subjects, list):
            continue
        if any(
            isinstance(subject, dict)
            and isinstance(subject.get("digest"), dict)
            and subject["digest"].get("sha256") == expected_artifact_digest
            for subject in subjects
        ):
            statements.append(statement)
    if not statements:
        raise ValueError("attestation subject does not match release artifact")
    return statements


def _require_matching_spdx_predicate(
    statements: list[dict[str, Any]], expected_digest: str
) -> None:
    """Require one subject-matched signed SPDX predicate to match the retained SBOM."""
    for statement in statements:
        if "predicate" not in statement:
            continue
        if semantic_json_sha256(statement["predicate"]) == expected_digest:
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
            chunk_size = os.write(descriptor, view[written:])
            if chunk_size <= 0:
                raise OSError("unable to make progress writing verification output")
            written += chunk_size
        os.fsync(descriptor)
        path_stat = os.stat(path, follow_symlinks=False)
        if not stat.S_ISREG(path_stat.st_mode):
            raise ValueError(f"verification output path stopped being regular: {path}")
        if (opened_stat.st_dev, opened_stat.st_ino) != (
            path_stat.st_dev,
            path_stat.st_ino,
        ):
            message = f"verification output path changed while being written: {path}"
            raise ValueError(message)
    finally:
        os.close(descriptor)


def _is_lower_sha256(value: str) -> bool:
    """Return whether a value is an exact lowercase SHA-256 hexadecimal digest."""
    return len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def main(argv: list[str]) -> int:
    """Verify stdin and retain it only after all requested semantic checks pass."""
    if len(argv) not in {3, 4}:
        print(
            "usage: verify_attestation_output.py OUTPUT_PATH "
            "EXPECTED_ARTIFACT_DIGEST [EXPECTED_SBOM_DIGEST]",
            file=sys.stderr,
        )
        return 2

    output_path = Path(argv[1])
    expected_artifact_digest = argv[2]
    expected_sbom_digest = argv[3] if len(argv) == 4 else None
    if not _is_lower_sha256(expected_artifact_digest):
        print("expected artifact digest must be lowercase SHA-256 hex", file=sys.stderr)
        return 1
    if expected_sbom_digest is not None and not _is_lower_sha256(expected_sbom_digest):
        print("expected SBOM digest must be lowercase SHA-256 hex", file=sys.stderr)
        return 1

    try:
        data = _read_bounded_stdin()
        verification = _require_nonempty_verification_array(load_strict_json(data))
        statements = _matching_artifact_statements(
            verification, expected_artifact_digest
        )
        if expected_sbom_digest is not None:
            _require_matching_spdx_predicate(statements, expected_sbom_digest)
        _write_exclusive_regular_file(output_path, data)
    except (OSError, UnicodeError, ValueError) as exc:
        message = f"unable to verify/retain attestation evidence strictly: {exc}"
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
