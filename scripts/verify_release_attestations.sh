#!/usr/bin/env bash
set -euo pipefail

: "${SOURCE_SHA:?SOURCE_SHA is required}"
: "${SOURCE_REF:?SOURCE_REF is required}"
: "${EXPECTED_SOURCE_REF:?EXPECTED_SOURCE_REF is required}"
: "${REPOSITORY:?REPOSITORY is required}"
: "${SIGNER_WORKFLOW:?SIGNER_WORKFLOW is required}"
: "${SPDX_PREDICATE:?SPDX_PREDICATE is required}"
: "${EXPECTED_PACKAGE_SNAPSHOT:?EXPECTED_PACKAGE_SNAPSHOT is required}"

EVIDENCE_DIR="${EVIDENCE_DIR:-evidence}"
VERIFICATION_DIR="${VERIFICATION_DIR:-attestation-verification}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROVENANCE_PREDICATE="https://slsa.dev/provenance/v1"

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

snapshot_package_evidence() {
  PYTHONPATH="$SCRIPT_DIR/../src" python - "$EVIDENCE_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from cwl_context_contracts.package_evidence_verifier import (
    PackageEvidenceInputError,
    verify_package_evidence_directory,
)


try:
    report = verify_package_evidence_directory(Path(sys.argv[1]))
except PackageEvidenceInputError as exc:
    print(f"unable to snapshot package evidence strictly: {exc.error_code}", file=sys.stderr)
    raise SystemExit(1) from exc
if not report.verified:
    mismatches = ",".join(report.mismatches)
    print(f"package evidence is not internally coherent: {mismatches}", file=sys.stderr)
    raise SystemExit(1)
print(json.dumps(report.to_mapping(), sort_keys=True, separators=(",", ":")))
PY
}

normalize_package_snapshot() {
  PYTHONPATH="$SCRIPT_DIR" python - "$1" <<'PY'
from __future__ import annotations

import json
import sys

from strict_json_identity import load_strict_json


try:
    snapshot = load_strict_json(sys.argv[1].encode("utf-8"))
except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
    print(f"build package snapshot is malformed: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc
if not isinstance(snapshot, dict) or snapshot.get("verified") is not True:
    print("build package snapshot is not a verified report", file=sys.stderr)
    raise SystemExit(1)
print(json.dumps(snapshot, sort_keys=True, separators=(",", ":")))
PY
}

artifact_digest_from_snapshot() {
  python - "$1" "$2" <<'PY'
from __future__ import annotations

import json
import sys


snapshot = json.loads(sys.argv[1])
artifact_name = sys.argv[2]
matches = [
    artifact["sha256"]
    for artifact in snapshot["artifacts"]
    if artifact["name"] == artifact_name
]
if len(matches) != 1:
    print(f"package snapshot does not identify artifact exactly once: {artifact_name}", file=sys.stderr)
    raise SystemExit(1)
print(matches[0])
PY
}

snapshot_spdx_semantic_digest() {
  PYTHONPATH="$SCRIPT_DIR" python - "$sbom_path" "$1" <<'PY'
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from strict_json_identity import (
    load_strict_json,
    read_stable_regular_file,
    semantic_json_sha256,
)


path = Path(sys.argv[1])
expected_raw_digest = sys.argv[2]
try:
    data = read_stable_regular_file(path, label="downloaded SPDX evidence")
    raw_digest = hashlib.sha256(data).hexdigest()
    if raw_digest != expected_raw_digest:
        raise ValueError("downloaded SPDX bytes do not match package snapshot")
    value = load_strict_json(data)
    if not isinstance(value, dict):
        raise ValueError("downloaded SPDX evidence must be a JSON object")
except (OSError, UnicodeError, ValueError) as exc:
    print(f"unable to snapshot downloaded SPDX evidence strictly: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc
print(semantic_json_sha256(value))
PY
}

expected_package_snapshot="$(normalize_package_snapshot "$EXPECTED_PACKAGE_SNAPSHOT")"
initial_package_snapshot="$(snapshot_package_evidence)"
if [[ "$initial_package_snapshot" != "$expected_package_snapshot" ]]; then
  echo "package evidence changed since build verification" >&2
  exit 1
fi
expected_sbom_raw_digest="$(
  artifact_digest_from_snapshot "$expected_package_snapshot" "$(basename "$sbom_path")"
)"
expected_sbom_digest="$(snapshot_spdx_semantic_digest "$expected_sbom_raw_digest")"

if [[ -e "$VERIFICATION_DIR" || -L "$VERIFICATION_DIR" ]]; then
  echo "verification directory must not pre-exist" >&2
  exit 1
fi
umask 077
mkdir "$VERIFICATION_DIR"

common_policy=(
  --repo "$REPOSITORY"
  --source-digest "$SOURCE_SHA"
  --source-ref "$EXPECTED_SOURCE_REF"
  --signer-digest "$SOURCE_SHA"
  --signer-workflow "$SIGNER_WORKFLOW"
  --cert-oidc-issuer https://token.actions.githubusercontent.com
  --deny-self-hosted-runners
)

for artifact in "${artifacts[@]}"; do
  artifact_name="$(basename "$artifact")"
  expected_artifact_digest="$(
    artifact_digest_from_snapshot "$expected_package_snapshot" "$artifact_name"
  )"
  gh attestation verify "$artifact" \
    "${common_policy[@]}" \
    --predicate-type="$PROVENANCE_PREDICATE" \
    --format json \
    | python "$SCRIPT_DIR/verify_attestation_output.py" \
        "$VERIFICATION_DIR/$artifact_name.provenance.json" \
        "$expected_artifact_digest" \
        "$PROVENANCE_PREDICATE"

  sbom_verification="$VERIFICATION_DIR/$artifact_name.sbom.json"
  gh attestation verify "$artifact" \
    "${common_policy[@]}" \
    --predicate-type "$SPDX_PREDICATE" \
    --format json \
    | python "$SCRIPT_DIR/verify_attestation_output.py" \
        "$sbom_verification" \
        "$expected_artifact_digest" \
        "$SPDX_PREDICATE" \
        "$expected_sbom_digest"
done

final_package_snapshot="$(snapshot_package_evidence)"
final_sbom_digest="$(snapshot_spdx_semantic_digest "$expected_sbom_raw_digest")"
if [[ "$final_package_snapshot" != "$expected_package_snapshot" \
   || "$final_sbom_digest" != "$expected_sbom_digest" ]]; then
  echo "package evidence changed during attestation verification" >&2
  exit 1
fi
