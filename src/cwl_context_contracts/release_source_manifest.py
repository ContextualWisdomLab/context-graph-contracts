"""Build an attestable manifest binding release package bytes to protected source."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

_MANIFEST_FORMAT = "cwl-context-release-source-manifest/v1"
_PACKAGE_VERIFICATION_FORMAT = "cwl-context-package-evidence-verification/v1"
_DISTRIBUTION_NAME = "cwl-context-contracts"
_REPOSITORY = "ContextualWisdomLab/context-graph-contracts"
_PROTECTED_SOURCE_REF = "refs/heads/main"
_SIGNER_WORKFLOW = f"{_REPOSITORY}/.github/workflows/supply-chain.yml"
_SBOM_NAME = "cwl-context-contracts.spdx.json"
_MAX_SNAPSHOT_BYTES = 1024 * 1024
_MAX_JSON_DEPTH = 64
_PACKAGE_NEXT_ACTION = (
    "verify artifact attestations bind these exact package bytes to the intended "
    "protected main source commit before release"
)
_NEXT_ACTION = (
    "independently verify this manifest's artifact attestation against the same "
    "repository, protected ref, source SHA, and signer workflow before treating "
    "its source fields as release provenance"
)
_INPUT_ACTION = (
    "provide one verified package-evidence snapshot and exact source identity"
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_WHEEL_PATTERN = re.compile(
    r"^cwl_context_contracts-([0-9]+\.[0-9]+\.[0-9]+)-"
    r"[^-]+-[^-]+-[^-]+\.whl$"
)
_SDIST_PATTERN = re.compile(
    r"^cwl_context_contracts-([0-9]+\.[0-9]+\.[0-9]+)\.tar\.gz$"
)
_SNAPSHOT_FIELDS = {
    "verification_format",
    "verified",
    "artifacts",
    "mismatches",
    "next_action",
}


class ReleaseSourceManifestInputError(ValueError):
    """Report malformed or unauthorized release-source manifest input."""

    def __init__(self, error_code: str) -> None:
        """Create an input error with a stable machine-readable error code."""
        super().__init__(error_code)
        self.error_code = error_code


@dataclass(frozen=True, slots=True)
class ReleaseSourceArtifact:
    """Exact SHA-256 identity for one package or SBOM artifact."""

    name: str
    sha256: str

    def to_mapping(self) -> dict[str, str]:
        """Return stable JSON-native artifact identity."""
        return {"name": self.name, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class ReleaseSourceManifest:
    """Attestable package/source binding that is not trusted until verified."""

    distribution_version: str
    source_repository: str
    source_ref: str
    source_commit_sha: str
    signer_workflow: str
    package_snapshot_sha256: str
    artifacts: tuple[ReleaseSourceArtifact, ...]

    def to_mapping(self) -> dict[str, object]:
        """Return the deterministic release-source manifest payload."""
        return {
            "manifest_format": _MANIFEST_FORMAT,
            "distribution_name": _DISTRIBUTION_NAME,
            "distribution_version": self.distribution_version,
            "release_tag": f"v{self.distribution_version}",
            "source_repository": self.source_repository,
            "source_ref": self.source_ref,
            "source_commit_sha": self.source_commit_sha,
            "signer_workflow": self.signer_workflow,
            "algorithm": "sha256",
            "package_snapshot_sha256": self.package_snapshot_sha256,
            "artifacts": [artifact.to_mapping() for artifact in self.artifacts],
            "next_action": _NEXT_ACTION,
        }


def _require(condition: bool, error_code: str) -> None:
    """Raise one stable input error when a release contract is not satisfied."""
    if not condition:
        raise ReleaseSourceManifestInputError(error_code)


def _validated_artifacts(
    package_snapshot: Mapping[str, object],
) -> tuple[tuple[ReleaseSourceArtifact, ...], str]:
    """Return exact release artifacts and their single semantic version."""
    _require(set(package_snapshot) == _SNAPSHOT_FIELDS, "package_snapshot_invalid")
    _require(
        package_snapshot.get("verification_format") == _PACKAGE_VERIFICATION_FORMAT,
        "package_snapshot_invalid",
    )
    _require(
        package_snapshot.get("verified") is True
        and package_snapshot.get("mismatches") == [],
        "package_snapshot_not_verified",
    )
    _require(
        package_snapshot.get("next_action") == _PACKAGE_NEXT_ACTION,
        "package_snapshot_invalid",
    )
    raw_artifacts = package_snapshot.get("artifacts")
    _require(
        isinstance(raw_artifacts, list) and len(raw_artifacts) == 3,
        "package_snapshot_artifacts_invalid",
    )

    artifacts: list[ReleaseSourceArtifact] = []
    for raw_artifact in raw_artifacts:
        _require(
            isinstance(raw_artifact, Mapping)
            and set(raw_artifact) == {"name", "sha256"},
            "package_snapshot_artifacts_invalid",
        )
        name = raw_artifact.get("name")
        digest = raw_artifact.get("sha256")
        _require(
            isinstance(name, str)
            and isinstance(digest, str)
            and _SHA256_PATTERN.fullmatch(digest) is not None,
            "package_snapshot_artifacts_invalid",
        )
        artifacts.append(ReleaseSourceArtifact(name=name, sha256=digest))

    names = [artifact.name for artifact in artifacts]
    _require(len(set(names)) == len(names), "package_snapshot_artifacts_invalid")
    wheel_names = [name for name in names if name.endswith(".whl")]
    sdist_names = [name for name in names if name.endswith(".tar.gz")]
    _require(
        len(wheel_names) == 1
        and len(sdist_names) == 1
        and names.count(_SBOM_NAME) == 1,
        "package_snapshot_artifacts_invalid",
    )
    wheel_match = _WHEEL_PATTERN.fullmatch(wheel_names[0])
    sdist_match = _SDIST_PATTERN.fullmatch(sdist_names[0])
    _require(
        wheel_match is not None
        and sdist_match is not None
        and wheel_match.group(1) == sdist_match.group(1),
        "package_snapshot_artifacts_invalid",
    )
    distribution_version = wheel_match.group(1)
    return tuple(artifacts), distribution_version


def build_release_source_manifest(
    package_snapshot: Mapping[str, object],
    *,
    source_repository: str,
    source_ref: str,
    source_commit_sha: str,
    signer_workflow: str,
) -> ReleaseSourceManifest:
    """Bind one verified package snapshot to the only authorized release source."""
    _require(source_repository == _REPOSITORY, "source_repository_invalid")
    _require(source_ref == _PROTECTED_SOURCE_REF, "source_ref_invalid")
    _require(
        _SOURCE_SHA_PATTERN.fullmatch(source_commit_sha) is not None,
        "source_commit_sha_invalid",
    )
    _require(signer_workflow == _SIGNER_WORKFLOW, "signer_workflow_invalid")
    artifacts, distribution_version = _validated_artifacts(package_snapshot)
    canonical_snapshot = json.dumps(
        package_snapshot,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return ReleaseSourceManifest(
        distribution_version=distribution_version,
        source_repository=source_repository,
        source_ref=source_ref,
        source_commit_sha=source_commit_sha,
        signer_workflow=signer_workflow,
        package_snapshot_sha256=hashlib.sha256(canonical_snapshot).hexdigest(),
        artifacts=artifacts,
    )


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build a JSON object while rejecting ambiguous duplicate member names."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object member: {key}")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(value: str) -> object:
    """Reject Python JSON extensions such as NaN and Infinity."""
    raise ValueError(f"non-standard JSON constant: {value}")


def _enforce_json_depth(text: str) -> None:
    """Reject structural nesting deeper than the release-input contract allows."""
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
            continue
        if character in "[{":
            depth += 1
            if depth > _MAX_JSON_DEPTH:
                raise ReleaseSourceManifestInputError("package_snapshot_too_deep")
        elif character in "]}":
            depth -= 1


def _load_package_snapshot(path: Path) -> Mapping[str, object]:
    """Load one bounded UTF-8 strict JSON snapshot or report a stable error."""
    try:
        with path.open("rb") as handle:
            snapshot_bytes = handle.read(_MAX_SNAPSHOT_BYTES + 1)
    except OSError:
        raise ReleaseSourceManifestInputError("package_snapshot_unreadable") from None
    if len(snapshot_bytes) > _MAX_SNAPSHOT_BYTES:
        raise ReleaseSourceManifestInputError("package_snapshot_too_large")
    try:
        snapshot_text = snapshot_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ReleaseSourceManifestInputError("package_snapshot_invalid") from None
    _enforce_json_depth(snapshot_text)
    try:
        payload = json.loads(
            snapshot_text,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except (ValueError, json.JSONDecodeError, RecursionError):
        raise ReleaseSourceManifestInputError("package_snapshot_invalid") from None
    if not isinstance(payload, Mapping):
        raise ReleaseSourceManifestInputError("package_snapshot_invalid")
    return payload


def _input_failure(error: str) -> int:
    """Print one machine-readable input failure and return exit two."""
    print(
        json.dumps(
            {
                "manifest_format": _MANIFEST_FORMAT,
                "generated": False,
                "error": error,
                "next_action": _INPUT_ACTION,
            },
            sort_keys=True,
        )
    )
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    """Build deterministic JSON for an externally attested release-source manifest."""
    parser = argparse.ArgumentParser(
        description=(
            "Bind verified CWL Context Graph package evidence to the exact protected "
            "source identity before attesting the resulting manifest."
        )
    )
    parser.add_argument("package_snapshot", type=Path)
    parser.add_argument("--source-repository", required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--signer-workflow", required=True)
    args = parser.parse_args(argv)

    try:
        package_snapshot = _load_package_snapshot(args.package_snapshot)
        manifest = build_release_source_manifest(
            package_snapshot,
            source_repository=args.source_repository,
            source_ref=args.source_ref,
            source_commit_sha=args.source_sha,
            signer_workflow=args.signer_workflow,
        )
    except ReleaseSourceManifestInputError as exc:
        return _input_failure(exc.error_code)

    print(json.dumps(manifest.to_mapping(), sort_keys=True))
    return 0
