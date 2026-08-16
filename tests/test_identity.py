"""Canonical authority and asset URI tests."""

from uuid import UUID

import pytest

from cwl_context_contracts import CanonicalAssetUri, CanonicalAuthorityUri
from tests.conftest import UUID7_TEXT


def test_authority_build_parse_and_render_round_trip() -> None:
    """A valid tenant-scoped authority identifier round-trips exactly."""
    value = CanonicalAuthorityUri.build(
        tenant_id="tenant_001",
        authority="sdp_core",
    )
    assert str(value) == "urn:cwl:tenant_001:sdp_core"
    assert CanonicalAuthorityUri.parse(str(value)) == value


def test_asset_build_parse_and_render_round_trip() -> None:
    """A valid UUIDv7-backed asset identifier round-trips exactly."""
    value = CanonicalAssetUri.build(
        tenant_id="tenant_001",
        authority="sdp_core",
        object_type="data_table",
        object_id=UUID7_TEXT,
    )
    assert str(CanonicalAssetUri.parse(str(value))) == str(value)
    assert value.object_id == UUID(UUID7_TEXT)
    assert value.authority_uri == CanonicalAuthorityUri("tenant_001", "sdp_core")


@pytest.mark.parametrize("field", ["Tenant", "a", "has-hyphen", "x" * 64])
def test_authority_build_rejects_invalid_segments(field: str) -> None:
    """Authority URI segments must use bounded lower-snake identifiers."""
    with pytest.raises(ValueError, match="lower snake"):
        CanonicalAuthorityUri.build(tenant_id=field, authority="ea_core")


def test_authority_parse_rejects_asset_uri() -> None:
    """Authority parsing does not accept an asset identifier."""
    with pytest.raises(ValueError, match="authority"):
        CanonicalAuthorityUri.parse(
            "urn:cwl:tenant_001:ea_core:application_record:" + UUID7_TEXT
        )


@pytest.mark.parametrize("field", ["Tenant", "a", "has-hyphen", "x" * 64])
def test_asset_build_rejects_invalid_segments(field: str) -> None:
    """Asset URI segments must use bounded lower-snake identifiers."""
    with pytest.raises(ValueError, match="lower snake"):
        CanonicalAssetUri.build(
            tenant_id=field,
            authority="ea_core",
            object_type="application_record",
            object_id=UUID7_TEXT,
        )


@pytest.mark.parametrize(
    "value",
    [
        "not-a-uuid",
        "550e8400-e29b-41d4-a716-446655440000",
        None,
    ],
)
def test_asset_build_rejects_non_uuid7(value: object) -> None:
    """Only RFC 9562 UUIDv7 values are accepted."""
    with pytest.raises(ValueError, match="UUIDv7|RFC 9562"):
        CanonicalAssetUri.build(
            tenant_id="tenant_001",
            authority="ea_core",
            object_type="application_record",
            object_id=value,  # type: ignore[arg-type]
        )


def test_asset_parse_rejects_noncanonical_text() -> None:
    """Asset parsing does not normalize encoded delimiters or uppercase text."""
    with pytest.raises(ValueError, match="asset"):
        CanonicalAssetUri.parse(
            "urn:cwl:tenant_001:EA_CORE:application_record:" + UUID7_TEXT
        )
