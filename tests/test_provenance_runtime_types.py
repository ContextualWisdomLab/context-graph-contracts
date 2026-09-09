"""Runtime type-safety regressions for provenance references."""

import pytest

from cwl_context_contracts import ProvenanceReference


def test_provenance_reference_rejects_non_asset_evidence_reference() -> None:
    """A type annotation alone must not admit an arbitrary evidence string."""
    with pytest.raises(TypeError, match="evidence_ref"):
        ProvenanceReference("urn:cwl:not-an-asset", "a" * 64)  # type: ignore[arg-type]


def test_provenance_reference_rejects_non_string_digest(asset_uri) -> None:
    """Digest validation reports the contract field rather than regex internals."""
    with pytest.raises(TypeError, match="sha256"):
        ProvenanceReference(asset_uri, 1)  # type: ignore[arg-type]


def test_provenance_reference_rejects_non_string_locator(asset_uri) -> None:
    """Optional source locators accept only strings when present."""
    with pytest.raises(TypeError, match="source_locator"):
        ProvenanceReference(asset_uri, "a" * 64, 1)  # type: ignore[arg-type]
