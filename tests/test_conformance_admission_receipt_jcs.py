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


def _assert_invalid_shape(approved: dict[str, object]) -> None:
    """Assert that ambiguous receipt identity input fails closed."""
    with pytest.raises(ValueError, match="approved_manifest_invalid_shape"):
        cwl_context_contracts.build_packaged_conformance_admission_receipt(approved)


def test_receipt_rejects_nonstring_manifest_identity_field() -> None:
    """Receipt identity fields use the string value kinds defined by the manifest."""
    approved = _approved_manifest()
    approved["algorithm"] = 7

    _assert_invalid_shape(approved)


@pytest.mark.parametrize("profile_count", [True, 1.5, -1, 2**53])
def test_receipt_rejects_non_jcs_profile_count(profile_count: object) -> None:
    """Profile count stays a non-boolean exact-range JSON integer."""
    approved = _approved_manifest()
    approved["profile_count"] = profile_count

    _assert_invalid_shape(approved)


def test_receipt_rejects_unpaired_unicode_surrogate() -> None:
    """Invalid Unicode scalar data cannot enter an RFC 8785 receipt preimage."""
    approved = _approved_manifest()
    approved["distribution_version"] = "invalid-\ud800-version"

    _assert_invalid_shape(approved)


def test_receipt_rejects_non_list_profile_collection() -> None:
    """Profile evidence must preserve the manifest's ordered JSON array shape."""
    approved = _approved_manifest()
    approved["profiles"] = "not-a-list"

    _assert_invalid_shape(approved)


def test_receipt_rejects_non_object_profile_entry() -> None:
    """A profile receipt preimage cannot assign meaning to a non-object entry."""
    approved = _approved_manifest()
    approved["profiles"] = [None]
    approved["profile_count"] = 1

    _assert_invalid_shape(approved)


def test_receipt_rejects_unknown_profile_member() -> None:
    """Unknown profile members cannot acquire undocumented digest semantics."""
    approved = _approved_manifest()
    profiles = approved["profiles"]
    assert isinstance(profiles, list)
    profile = profiles[0]
    assert isinstance(profile, dict)
    profile["untrusted_extension"] = "value"

    _assert_invalid_shape(approved)


def test_receipt_rejects_nonstring_profile_name() -> None:
    """Profile names must remain JCS-safe strings."""
    approved = _approved_manifest()
    profiles = approved["profiles"]
    assert isinstance(profiles, list)
    profile = profiles[0]
    assert isinstance(profile, dict)
    profile["profile_name"] = 7

    _assert_invalid_shape(approved)


def test_receipt_rejects_unpaired_surrogate_in_profile_digest() -> None:
    """Every profile string is checked before canonical serialization."""
    approved = _approved_manifest()
    profiles = approved["profiles"]
    assert isinstance(profiles, list)
    profile = profiles[0]
    assert isinstance(profile, dict)
    profile["sha256"] = "invalid-\ud800-digest"

    _assert_invalid_shape(approved)
