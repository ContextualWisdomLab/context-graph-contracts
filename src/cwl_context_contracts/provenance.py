"""Evidence-addressing primitives aligned with W3C PROV-O semantics."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .identity import CanonicalAssetUri

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class ProvenanceReference:
    """Reference to source evidence and its exact byte digest."""

    evidence_ref: CanonicalAssetUri
    sha256: str
    source_locator: str | None = None

    def __post_init__(self) -> None:
        """Validate digest and optional locator bounds."""

        if not _SHA256_PATTERN.fullmatch(self.sha256):
            raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
        if self.source_locator is not None:
            if not self.source_locator or len(self.source_locator) > 2048:
                raise ValueError("source_locator must contain 1-2048 characters")
