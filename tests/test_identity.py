"""Canonical authority and asset URI tests."""

from uuid import UUID

import pytest

from cwl_context_contracts import CanonicalAssetUri, CanonicalAuthorityUri
from tests.conftest import UUID7_TEXT

INVALID_SEGMENTS = [
    "Tenant",
    "a",
    "has-hyphen",
    "x" * 64,
    "tenant__001",
    "tenant_",
    "t_enant",
]


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


@pytest.mark.parametrize("field", INVALID_SEGMENTS)
def test_authority_build_rejects_invalid_segments(field: str) -> None:
    """Authority URI segments must use bounded canonical lower-snake words."""
    with pytest.raises(ValueError, match="lower snake"):
        CanonicalAuthorityUri.build(tenant_id=field, authority="ea_core")


@pytest.mark.parametrize("field", INVALID_SEGMENTS)
def test_authority_parse_rejects_invalid_segments(field: str) -> None:
    """Authority parsing rejects ambiguous lower-snake spellings."""
    with pytest.raises(ValueError, match="authority"):
        CanonicalAuthorityUri.parse(f"urn:cwl:{field}:ea_core")


def test_authority_parse_rejects_asset_uri() -> None:
    """Authority parsing does not accept an asset identifier."""
    with pytest.raises(ValueError, match="authority"):
        CanonicalAuthorityUri.parse(
            "urn:cwl:tenant_001:ea_core:application_record:" + UUID7_TEXT
        )


@pytest.mark.parametrize("field_name", ["tenant_id", "authority"])
def test_authority_build_rejects_non_string_segments(field_name: str) -> None:
    """Authority construction rejects non-string components deliberately."""
    kwargs: dict[str, object] = {
        "tenant_id": "tenant_001",
        "authority": "ea_core",
    }
    kwargs[field_name] = 1
    with pytest.raises(TypeError, match=field_name):
        CanonicalAuthorityUri.build(**kwargs)  # type: ignore[arg-type]


def test_authority_parse_rejects_non_string_input() -> None:
    """Authority parsing rejects non-string input at the public boundary."""
    with pytest.raises(TypeError, match="value"):
        CanonicalAuthorityUri.parse(1)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", INVALID_SEGMENTS)
def test_asset_build_rejects_invalid_segments(field: str) -> None:
    """Asset URI segments must use bounded canonical lower-snake words."""
    with pytest.raises(ValueError, match="lower snake"):
        CanonicalAssetUri.build(
            tenant_id=field,
            authority="ea_core",
            object_type="application_record",
            object_id=UUID7_TEXT,
        )


@pytest.mark.parametrize("field", INVALID_SEGMENTS)
def test_asset_parse_rejects_invalid_segments(field: str) -> None:
    """Asset parsing rejects ambiguous lower-snake spellings."""
    with pytest.raises(ValueError, match="asset"):
        CanonicalAssetUri.parse(
            f"urn:cwl:{field}:ea_core:application_record:{UUID7_TEXT}"
        )


@pytest.mark.parametrize("field_name", ["tenant_id", "authority", "object_type"])
def test_asset_build_rejects_non_string_segments(field_name: str) -> None:
    """Asset construction rejects non-string components deliberately."""
    kwargs: dict[str, object] = {
        "tenant_id": "tenant_001",
        "authority": "ea_core",
        "object_type": "application_record",
        "object_id": UUID7_TEXT,
    }
    kwargs[field_name] = 1
    with pytest.raises(TypeError, match=field_name):
        CanonicalAssetUri.build(**kwargs)  # type: ignore[arg-type]


def test_asset_parse_rejects_non_string_input() -> None:
    """Asset parsing rejects non-string input at the public boundary."""
    with pytest.raises(TypeError, match="value"):
        CanonicalAssetUri.parse(1)  # type: ignore[arg-type]


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
