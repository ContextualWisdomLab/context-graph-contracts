"""Shared test fixtures."""

from uuid import UUID

import pytest

from cwl_context_contracts import CanonicalAssetUri, CanonicalAuthorityUri

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
