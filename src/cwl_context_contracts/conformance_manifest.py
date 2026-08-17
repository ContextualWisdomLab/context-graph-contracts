"""Integrity manifest for the exact semantic conformance profiles in a package."""

from __future__ import annotations

import json
from dataclasses import dataclass

from .conformance import (
    available_conformance_profile_names,
    conformance_profile_sha256,
)


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
    """Artifact-local integrity evidence for every packaged semantic profile."""

    profiles: tuple[ConformanceProfileEvidence, ...]

    @property
    def profile_count(self) -> int:
        """Return the number of semantic profiles bound by this manifest."""
        return len(self.profiles)

    def to_mapping(self) -> dict[str, object]:
        """Return a stable machine-readable manifest for evidence capture."""
        return {
            "algorithm": "sha256",
            "profile_count": self.profile_count,
            "profiles": [profile.to_mapping() for profile in self.profiles],
        }


def build_packaged_conformance_manifest() -> ConformanceEvidenceManifest:
    """Build integrity evidence from the exact profile bytes in this installation."""
    return ConformanceEvidenceManifest(
        profiles=tuple(
            ConformanceProfileEvidence(
                profile_name=profile_name,
                sha256=conformance_profile_sha256(profile_name),
            )
            for profile_name in available_conformance_profile_names()
        )
    )


def main() -> int:
    """Print the installed profile manifest as deterministic JSON."""
    manifest = build_packaged_conformance_manifest()
    print(json.dumps(manifest.to_mapping(), sort_keys=True))
    return 0
