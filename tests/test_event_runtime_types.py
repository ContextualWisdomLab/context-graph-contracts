"""Runtime type-safety regressions for CloudEvents public construction."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from cwl_context_contracts import CloudEventEnvelope
from tests.conftest import EVENT_UUID7_TEXT


class _CanonicalLookalike:
    """Expose canonical-looking attributes without being a contract reference."""

    tenant_id = "tenant_001"

    def __str__(self) -> str:
        """Render a deliberately non-canonical value."""
        return "https://attacker.invalid/not-canonical"


def _event_kwargs(authority_uri, asset_uri) -> dict[str, object]:
    """Return valid constructor arguments that one test can selectively corrupt."""
    return {
        "event_id": UUID(EVENT_UUID7_TEXT),
        "source": authority_uri,
        "event_type": "org.contextualwisdomlab.ea.lifecycle.changed.v1",
        "subject": asset_uri,
        "event_time": datetime(2026, 8, 16, tzinfo=UTC),
        "data": {},
    }


@pytest.mark.parametrize("source_kind", ["string", "asset", "lookalike"])
def test_event_rejects_non_authority_source(
    authority_uri,
    asset_uri,
    source_kind,
) -> None:
    """Only a canonical authority reference can occupy the source field."""
    invalid_source = {
        "string": str(authority_uri),
        "asset": asset_uri,
        "lookalike": _CanonicalLookalike(),
    }[source_kind]
    kwargs = _event_kwargs(authority_uri, asset_uri)
    kwargs["source"] = invalid_source
    with pytest.raises(TypeError, match="source"):
        CloudEventEnvelope(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("subject_kind", ["string", "authority", "lookalike"])
def test_event_rejects_non_asset_subject(
    authority_uri,
    asset_uri,
    subject_kind,
) -> None:
    """Only a canonical asset reference can occupy the subject field."""
    invalid_subject = {
        "string": str(asset_uri),
        "authority": authority_uri,
        "lookalike": _CanonicalLookalike(),
    }[subject_kind]
    kwargs = _event_kwargs(authority_uri, asset_uri)
    kwargs["subject"] = invalid_subject
    with pytest.raises(TypeError, match="subject"):
        CloudEventEnvelope(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("event_type", 1),
        ("event_time", "2026-08-16T00:00:00Z"),
        ("data_schema", 1),
        ("extensions", []),
    ],
)
def test_event_rejects_invalid_public_field_types(
    authority_uri,
    asset_uri,
    field_name,
    field_value,
) -> None:
    """Public constructor fields fail with deliberate contract type errors."""
    kwargs = _event_kwargs(authority_uri, asset_uri)
    kwargs[field_name] = field_value
    with pytest.raises(TypeError, match=field_name):
        CloudEventEnvelope(**kwargs)  # type: ignore[arg-type]
