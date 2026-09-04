"""Cross-language JSON interoperability regressions."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from cwl_context_contracts import CloudEventEnvelope
from tests.conftest import EVENT_UUID7_TEXT

_MAX_EXACT_JSON_INTEGER = (2**53) - 1


def _event(authority_uri, asset_uri, data) -> CloudEventEnvelope:
    """Build one valid event around caller-supplied JSON data."""
    return CloudEventEnvelope(
        event_id=UUID(EVENT_UUID7_TEXT),
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data=data,
    )


@pytest.mark.parametrize(
    "value",
    [_MAX_EXACT_JSON_INTEGER, -_MAX_EXACT_JSON_INTEGER],
)
def test_event_preserves_exact_cross_language_integer_boundary(
    authority_uri,
    asset_uri,
    value: int,
) -> None:
    """RFC 8259's commonly interoperable exact integer range is preserved."""
    event = _event(authority_uri, asset_uri, {"nested": [{"count": value}]})

    assert event.to_mapping()["data"]["nested"][0]["count"] == value


@pytest.mark.parametrize(
    "value",
    [_MAX_EXACT_JSON_INTEGER + 1, -_MAX_EXACT_JSON_INTEGER - 1],
)
def test_event_rejects_integer_outside_exact_cross_language_range(
    authority_uri,
    asset_uri,
    value: int,
) -> None:
    """Provider-neutral events fail closed before integer precision can drift."""
    with pytest.raises(ValueError, match="exact interoperable range"):
        _event(authority_uri, asset_uri, {"nested": [{"count": value}]})
