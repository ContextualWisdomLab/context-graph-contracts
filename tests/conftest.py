"""Shared test fixtures."""

from uuid import UUID

import pytest
from jsonschema import FormatChecker

from cwl_context_contracts import (
    CanonicalAssetUri,
    CanonicalAuthorityUri,
    parse_rfc3339_timestamp,
)

RFC3339_FORMAT_CHECKER = FormatChecker()


@RFC3339_FORMAT_CHECKER.checks("date-time")
def _is_rfc3339_date_time(value: object) -> bool:
    """Apply the same RFC 3339 grammar used by the Python reference package."""
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    try:
        parse_rfc3339_timestamp(value)
    except ValueError:
        return False
    return True

UUID7_TEXT = "0195d145-64e8-7f4f-8a23-a0cc784cb711"
EVENT_UUID7_TEXT = "0195d145-64e8-7f4f-8a23-a0cc784cb799"


@pytest.fixture
def authority_uri() -> CanonicalAuthorityUri:
    """Return a stable authority URI fixture."""
    return CanonicalAuthorityUri.build(
        tenant_id="tenant_001",
        authority="ea_core",
    )


@pytest.fixture
def asset_uri() -> CanonicalAssetUri:
    """Return a stable canonical asset URI fixture."""
    return CanonicalAssetUri.build(
        tenant_id="tenant_001",
        authority="ea_core",
        object_type="application_record",
        object_id=UUID(UUID7_TEXT),
    )
