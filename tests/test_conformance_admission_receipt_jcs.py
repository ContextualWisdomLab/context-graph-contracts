"""Interoperability acceptance for RFC 8785 receipt preimages."""

from __future__ import annotations

import json

import pytest

import cwl_context_contracts


def _approved_manifest() -> dict[str, object]:
    """Return one mutable exact installed conformance manifest."""
    return json.loads(
        json.dumps(cwl_context_contracts.build_packaged_conformance_manifest().to_mapping())
    )


def test_receipt_rejects_integer_outside_exact_json_interoperability_range() -> None:
    """A non-I-JSON count cannot become an RFC 8785 receipt preimage."""
    approved = _approved_manifest()
    approved["profile_count"] = 2**53

    with pytest.raises(ValueError, match="approved_manifest_invalid_shape"):
        cwl_context_contracts.build_packaged_conformance_admission_receipt(approved)


def test_receipt_rejects_unpaired_unicode_surrogate() -> None:
    """Invalid Unicode scalar data cannot enter an RFC 8785 receipt preimage."""
    approved = _approved_manifest()
    approved["distribution_version"] = "invalid-\ud800-version"

    with pytest.raises(ValueError, match="approved_manifest_invalid_shape"):
        cwl_context_contracts.build_packaged_conformance_admission_receipt(approved)
