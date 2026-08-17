"""Integrity manifest for the exact semantic conformance profiles in a package."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.metadata import version

from .conformance import (
    available_conformance_profile_names,
    conformance_profile_sha256,
)

_MANIFEST_FORMAT = "cwl-context-conformance-manifest/v1"
_DISTRIBUTION_NAME = "cwl-context-contracts"


@dataclass(frozen=True, slots=True)
class ConformanceProfileEvidence:
    """SHA-256 evidence for one exact packaged semantic conformance profile."""

    profile_name: str
    sha256: str

    def to_mapping(self) -> dict[str, str]:
        """Return a deterministic JSON-native evidence record."""
        return {
            "profile_name": self.profile_name,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class ConformanceEvidenceManifest:
    """Version-bound artifact integrity evidence for packaged semantic profiles."""

    distribution_name: str
    distribution_version: str
    profiles: tuple[ConformanceProfileEvidence, ...]

    @property
    def profile_count(self) -> int:
        """Return the number of semantic profiles bound by this manifest."""
        return len(self.profiles)

    def to_mapping(self) -> dict[str, object]:
        """Return a stable machine-readable manifest for evidence capture."""
        return {
            "manifest_format": _MANIFEST_FORMAT,
            "distribution_name": self.distribution_name,
            "distribution_version": self.distribution_version,
            "algorithm": "sha256",
            "profile_count": self.profile_count,
            "profiles": [profile.to_mapping() for profile in self.profiles],
        }


def build_packaged_conformance_manifest() -> ConformanceEvidenceManifest:
    """Build version-bound integrity evidence from this installed distribution."""
    return ConformanceEvidenceManifest(
        distribution_name=_DISTRIBUTION_NAME,
        distribution_version=version(_DISTRIBUTION_NAME),
        profiles=tuple(
            ConformanceProfileEvidence(
                profile_name=profile_name,
                sha256=conformance_profile_sha256(profile_name),
            )
            for profile_name in available_conformance_profile_names()
        ),
    )


def main() -> int:
    """Print the installed profile manifest as deterministic JSON."""
    manifest = build_packaged_conformance_manifest()
    print(json.dumps(manifest.to_mapping(), sort_keys=True))
    return 0
