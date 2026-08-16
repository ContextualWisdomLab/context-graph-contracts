"""Evidence-addressing primitives aligned with W3C PROV-O semantics."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .identity import CanonicalAssetUri

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_PROVENANCE_FIELDS = frozenset({"evidence_ref", "sha256", "source_locator"})


@dataclass(frozen=True, slots=True)
class ProvenanceReference:
    """Reference to source evidence and its exact byte digest."""

    evidence_ref: CanonicalAssetUri
    sha256: str
    source_locator: str | None = None

    def __post_init__(self) -> None:
        """Validate evidence identity, digest, and optional locator bounds."""
        if not isinstance(self.evidence_ref, CanonicalAssetUri):
            raise TypeError("evidence_ref must be a CanonicalAssetUri")
        if not isinstance(self.sha256, str):
            raise TypeError("sha256 must be a string")
        if not _SHA256_PATTERN.fullmatch(self.sha256):
            raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
        if self.source_locator is not None:
            if not isinstance(self.source_locator, str):
                raise TypeError("source_locator must be a string when present")
            if not self.source_locator or len(self.source_locator) > 2048:
                raise ValueError("source_locator must contain 1-2048 characters")

    def to_mapping(self) -> dict[str, str | None]:
        """Serialize the evidence reference to JSON-native fields."""
        return {
            "evidence_ref": str(self.evidence_ref),
            "sha256": self.sha256,
            "source_locator": self.source_locator,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ProvenanceReference:
        """Parse one coherent snapshot of a provenance-reference mapping."""
        if not isinstance(value, Mapping):
            raise TypeError("value must be a mapping")
        snapshot = dict(value.items())
        unknown = snapshot.keys() - _PROVENANCE_FIELDS
        if unknown:
            raise ValueError(f"unknown provenance fields: {sorted(unknown)!r}")
        if "evidence_ref" not in snapshot or "sha256" not in snapshot:
            raise ValueError("provenance requires evidence_ref and sha256")
        raw_locator = snapshot.get("source_locator")
        return cls(
            evidence_ref=CanonicalAssetUri.parse(snapshot["evidence_ref"]),
            sha256=snapshot["sha256"],
            source_locator=raw_locator,
        )
