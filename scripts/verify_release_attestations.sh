#!/usr/bin/env bash
set -euo pipefail

: "${SOURCE_SHA:?SOURCE_SHA is required}"
: "${SOURCE_REF:?SOURCE_REF is required}"
: "${EXPECTED_SOURCE_REF:?EXPECTED_SOURCE_REF is required}"
: "${REPOSITORY:?REPOSITORY is required}"
: "${SIGNER_WORKFLOW:?SIGNER_WORKFLOW is required}"
: "${SPDX_PREDICATE:?SPDX_PREDICATE is required}"

EVIDENCE_DIR="${EVIDENCE_DIR:-evidence}"
VERIFICATION_DIR="${VERIFICATION_DIR:-attestation-verification}"

if [[ "$SOURCE_REF" != "$EXPECTED_SOURCE_REF" ]]; then
  echo "refusing attestation verification outside protected main" >&2
  exit 1
fi

if [[ ! "$SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]]; then
  echo "source SHA must be an exact lowercase 40-hex commit" >&2
  exit 1
fi

shopt -s nullglob
wheels=("$EVIDENCE_DIR"/*.whl)
sdists=("$EVIDENCE_DIR"/*.tar.gz)
if (( ${#wheels[@]} != 1 || ${#sdists[@]} != 1 )); then
  echo "expected exactly one wheel and one source distribution" >&2
  exit 1
fi
artifacts=("${wheels[@]}" "${sdists[@]}")

sbom_path="$EVIDENCE_DIR/cwl-context-contracts.spdx.json"
if [[ ! -f "$sbom_path" || -L "$sbom_path" ]]; then
  echo "expected one regular downloaded SPDX evidence document" >&2
  exit 1
fi

mkdir -p "$VERIFICATION_DIR"
common_policy=(
  --repo "$REPOSITORY"
  --source-digest "$SOURCE_SHA"
  --source-ref "$EXPECTED_SOURCE_REF"
  --signer-digest "$SOURCE_SHA"
  --signer-workflow "$SIGNER_WORKFLOW"
  --cert-oidc-issuer https://token.actions.githubusercontent.com
  --deny-self-hosted-runners
)

verify_attested_sbom_matches_downloaded_evidence() {
  local verification_path="$1"
  python - "$sbom_path" "$verification_path" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


class DuplicateJsonMember(ValueError):
    """Reject ambiguous JSON objects with duplicate member names."""


def reject_duplicate_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object only when every member name is unique."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonMember(f"duplicate JSON member: {key}")
        result[key] = value
    return result


def reject_nonstandard_constant(value: str) -> None:
    """Reject NaN and Infinity extensions that are not valid JSON."""
    raise ValueError(f"non-standard JSON numeric constant: {value}")


def load_strict_json(path: Path) -> Any:
    """Parse one bounded evidence document with strict JSON member semantics."""
    data = path.read_bytes()
    if len(data) > 16 * 1024 * 1024:
        raise ValueError(f"JSON evidence exceeds 16 MiB: {path}")
    return json.loads(
        data.decode("utf-8"),
        object_pairs_hook=reject_duplicate_members,
        parse_constant=reject_nonstandard_constant,
    )


def normalized_json(value: Any) -> str:
    """Return deterministic JSON for exact parsed-value comparison."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


expected_path = Path(sys.argv[1])
verification_path = Path(sys.argv[2])
try:
    expected = load_strict_json(expected_path)
    verification = load_strict_json(verification_path)
except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
    print(f"unable to parse attestation/SBOM evidence strictly: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc

if not isinstance(expected, dict):
    print("downloaded SPDX evidence must be a JSON object", file=sys.stderr)
    raise SystemExit(1)
if not isinstance(verification, list) or not verification:
    print("gh attestation verification must return a non-empty JSON array", file=sys.stderr)
    raise SystemExit(1)

expected_normalized = normalized_json(expected)
for candidate in verification:
    if not isinstance(candidate, dict):
        continue
    result = candidate.get("verificationResult")
    if not isinstance(result, dict):
        continue
    statement = result.get("statement")
    if not isinstance(statement, dict) or "predicate" not in statement:
        continue
    if normalized_json(statement["predicate"]) == expected_normalized:
        raise SystemExit(0)

print(
    "attested SPDX predicate does not match downloaded package SBOM",
    file=sys.stderr,
)
raise SystemExit(1)
PY
}

for artifact in "${artifacts[@]}"; do
  artifact_name="$(basename "$artifact")"
  gh attestation verify "$artifact" \
    "${common_policy[@]}" \
    --format json \
    > "$VERIFICATION_DIR/$artifact_name.provenance.json"
  sbom_verification="$VERIFICATION_DIR/$artifact_name.sbom.json"
  gh attestation verify "$artifact" \
    "${common_policy[@]}" \
    --predicate-type "$SPDX_PREDICATE" \
    --format json \
    > "$sbom_verification"
  verify_attested_sbom_matches_downloaded_evidence "$sbom_verification"
done
