"""Verify release package bytes against the repository package-evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

_VERIFICATION_FORMAT = "cwl-context-package-evidence-verification/v1"
_DISTRIBUTION_PREFIX = "cwl_context_contracts-"
_SBOM_NAME = "cwl-context-contracts.spdx.json"
_CHECKSUM_NAME = "SHA256SUMS"
_CHECKSUM_PATTERN = re.compile(
    r"^([0-9a-f]{64}) [ *]([A-Za-z0-9][A-Za-z0-9._+-]*)$"
)
_ACCEPT_ACTION = (
    "verify artifact attestations bind these exact package bytes to the intended "
    "protected main source commit before release"
)
_REPAIR_ACTION = (
    "rebuild or reacquire exact package evidence before provenance and release "
    "verification"
)
_INPUT_ACTION = "provide a readable package-evidence directory"


class PackageEvidenceInputError(ValueError):
    """Report a malformed or unreadable package-evidence input boundary."""

    def __init__(self, error_code: str) -> None:
        """Create an input error with a stable machine-readable error code."""
        super().__init__(error_code)
        self.error_code = error_code


@dataclass(frozen=True, slots=True)
class PackageArtifactEvidence:
    """One exact artifact identity declared by ``SHA256SUMS``."""

    name: str
    sha256: str

    def to_mapping(self) -> dict[str, str]:
        """Return stable machine-readable artifact checksum evidence."""
        return {"name": self.name, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class PackageEvidenceVerification:
    """Deterministic decision for one downloaded package-evidence directory."""

    artifacts: tuple[PackageArtifactEvidence, ...]
    mismatches: tuple[str, ...]

    @property
    def verified(self) -> bool:
        """Return whether every required package-evidence check passed."""
        return not self.mismatches

    @property
    def next_action(self) -> str:
        """Return the smallest release-operator action for this decision."""
        return _ACCEPT_ACTION if self.verified else _REPAIR_ACTION

    def to_mapping(self) -> dict[str, object]:
        """Return stable machine-readable package-evidence verification."""
        return {
            "verification_format": _VERIFICATION_FORMAT,
            "verified": self.verified,
            "artifacts": [artifact.to_mapping() for artifact in self.artifacts],
            "mismatches": list(self.mismatches),
            "next_action": self.next_action,
        }


def _load_checksum_manifest(evidence_directory: Path) -> dict[str, str]:
    """Read strict GNU-style SHA256SUMS without accepting external paths."""
    checksum_path = evidence_directory / _CHECKSUM_NAME
    if checksum_path.is_symlink():
        raise PackageEvidenceInputError("checksum_manifest_unsafe")
    try:
        checksum_text = checksum_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PackageEvidenceInputError("checksum_manifest_unreadable") from exc

    checksums: dict[str, str] = {}
    for line in checksum_text.splitlines():
        match = _CHECKSUM_PATTERN.fullmatch(line)
        if match is None:
            raise PackageEvidenceInputError("checksum_manifest_invalid")
        digest, artifact_name = match.groups()
        if artifact_name in checksums:
            raise PackageEvidenceInputError("checksum_manifest_invalid")
        checksums[artifact_name] = digest
    if not checksums:
        raise PackageEvidenceInputError("checksum_manifest_invalid")
    return checksums


def _wheel_version(name: str) -> str | None:
    """Return the normalized wheel filename version or ``None`` for a wrong shape."""
    if not name.startswith(_DISTRIBUTION_PREFIX) or not name.endswith(".whl"):
        return None
    filename_parts = name[:-4].split("-")
    if len(filename_parts) not in {5, 6}:
        return None
    version = filename_parts[1]
    return version or None


def _sdist_version(name: str) -> str | None:
    """Return the normalized source-distribution filename version when present."""
    suffix = ".tar.gz"
    if not name.startswith(_DISTRIBUTION_PREFIX) or not name.endswith(suffix):
        return None
    version = name[len(_DISTRIBUTION_PREFIX) : -len(suffix)]
    if not version or "-" in version:
        return None
    return version


def _artifact_set_is_exact(checksums: dict[str, str]) -> bool:
    """Return whether checksums name one coherent wheel, sdist, and SPDX SBOM."""
    artifact_names = set(checksums)
    wheel_versions = {
        name: _wheel_version(name)
        for name in artifact_names
        if name.endswith(".whl")
    }
    sdist_versions = {
        name: _sdist_version(name)
        for name in artifact_names
        if name.endswith(".tar.gz")
    }
    if len(wheel_versions) != 1 or len(sdist_versions) != 1:
        return False
    wheel_name, wheel_version = next(iter(wheel_versions.items()))
    sdist_name, sdist_version = next(iter(sdist_versions.items()))
    return (
        wheel_version is not None
        and wheel_version == sdist_version
        and artifact_names == {wheel_name, sdist_name, _SBOM_NAME}
    )


def _sha256_file(path: Path) -> str:
    """Hash one regular artifact without loading the complete file into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _spdx_is_3_0_1_package_document(path: Path) -> bool:
    """Return whether the checked SBOM preserves this SPDX 3.0.1 package shape."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    expected_context = "https://spdx.org/rdf/3.0.1/spdx-context.jsonld"
    if payload.get("@context") != expected_context:
        return False
    graph = payload.get("@graph")
    if not isinstance(graph, list) or not graph:
        return False
    mapping_items = [item for item in graph if isinstance(item, dict)]
    has_creation_info = any(
        item.get("type") == "CreationInfo"
        and item.get("specVersion") == "3.0.1"
        for item in mapping_items
    )
    has_package = any(
        item.get("type") == "software_Package"
        and item.get("name") == "cwl-context-contracts"
        for item in mapping_items
    )
    return has_creation_info and has_package


def verify_package_evidence_directory(
    evidence_directory: Path,
) -> PackageEvidenceVerification:
    """Verify exact wheel, sdist, SPDX and SHA-256 evidence from a workflow bundle."""
    evidence_directory = Path(evidence_directory)
    if not evidence_directory.is_dir():
        raise PackageEvidenceInputError("evidence_directory_unreadable")

    checksums = _load_checksum_manifest(evidence_directory)
    artifacts = tuple(
        PackageArtifactEvidence(name=name, sha256=checksums[name])
        for name in sorted(checksums)
    )
    if not _artifact_set_is_exact(checksums):
        return PackageEvidenceVerification(
            artifacts=artifacts,
            mismatches=("artifact_set",),
        )

    mismatches: list[str] = []
    for artifact in artifacts:
        artifact_path = evidence_directory / artifact.name
        if artifact_path.is_symlink() or not artifact_path.is_file():
            mismatches.append(f"artifact_unsafe:{artifact.name}")
        elif _sha256_file(artifact_path) != artifact.sha256:
            mismatches.append(f"artifact_sha256:{artifact.name}")

    sbom_unsafe = f"artifact_unsafe:{_SBOM_NAME}" in mismatches
    sbom_path = evidence_directory / _SBOM_NAME
    if not sbom_unsafe and not _spdx_is_3_0_1_package_document(sbom_path):
        mismatches.append("sbom_spdx_3_0_1")

    return PackageEvidenceVerification(
        artifacts=artifacts,
        mismatches=tuple(mismatches),
    )


def _input_failure(error: str) -> int:
    """Print one machine-readable input failure and return exit two."""
    print(
        json.dumps(
            {
                "verification_format": _VERIFICATION_FORMAT,
                "verified": False,
                "error": error,
                "next_action": _INPUT_ACTION,
            },
            sort_keys=True,
        )
    )
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    """Verify one downloaded package-evidence directory and emit a JSON decision."""
    parser = argparse.ArgumentParser(
        description=(
            "Verify the exact wheel, source distribution, SPDX 3.0.1 SBOM, and "
            "SHA256SUMS emitted by the CWL Context Graph contract supply-chain job."
        )
    )
    parser.add_argument("evidence_directory", type=Path)
    args = parser.parse_args(argv)

    try:
        report = verify_package_evidence_directory(args.evidence_directory)
    except PackageEvidenceInputError as exc:
        return _input_failure(exc.error_code)

    print(json.dumps(report.to_mapping(), sort_keys=True))
    return 0 if report.verified else 1
