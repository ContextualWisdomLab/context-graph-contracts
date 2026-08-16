"""Provenance reference tests."""

import pytest

from cwl_context_contracts import ProvenanceReference


def test_provenance_reference_accepts_digest_and_locator(asset_uri) -> None:
    """A bounded locator and lowercase SHA-256 digest are accepted."""

    reference = ProvenanceReference(asset_uri, "a" * 64, "$.rows[0]")
    assert reference.evidence_ref == asset_uri
    assert reference.source_locator == "$.rows[0]"


def test_provenance_reference_allows_absent_locator(asset_uri) -> None:
    """A digest-only reference leaves the optional locator unset."""

    reference = ProvenanceReference(asset_uri, "b" * 64)
    assert reference.source_locator is None


@pytest.mark.parametrize("digest", ["A" * 64, "a" * 63, "z" * 64])
def test_provenance_reference_rejects_invalid_digest(asset_uri, digest: str) -> None:
    """Digest text must be exact lowercase SHA-256 hexadecimal."""

    with pytest.raises(ValueError, match="sha256"):
        ProvenanceReference(asset_uri, digest)


@pytest.mark.parametrize("locator", ["", "x" * 2049])
def test_provenance_reference_rejects_invalid_locator(asset_uri, locator: str) -> None:
    """Optional source locators are non-empty and bounded."""

    with pytest.raises(ValueError, match="source_locator"):
        ProvenanceReference(asset_uri, "a" * 64, locator)
