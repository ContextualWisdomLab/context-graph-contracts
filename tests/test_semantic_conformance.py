"""Provider-neutral semantic conformance vector regressions."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from cwl_context_contracts import (
    CloudEventEnvelope,
    ContextAssertion,
    available_conformance_profile_names,
    available_schema_names,
    load_conformance_profile,
    load_schema,
)
from tests.conftest import EVENT_UUID7_TEXT

_ASSERTION_PROFILE = "context-assertion-semantics.v1.json"
_DATA_MANAGEMENT_PROFILE = "data-management-assessment-semantics.v1.json"
_EVENT_PROFILE = "cloudevent-semantics.v1.json"
_JSON_PROFILE = "cwl-json-interoperability.v1.json"
_TIMESTAMP_PROFILE = "cwl-timestamp-profile.v1.json"


def _schema_registry() -> Registry:
    """Return every packaged schema as one Draft 2020-12 registry."""
    schemas = [load_schema(name) for name in available_schema_names()]
    return Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )


def test_conformance_profile_inventory_is_stable_and_complete() -> None:
    """Installed consumers can enumerate all semantic profiles deterministically."""
    assert available_conformance_profile_names() == (
        _TIMESTAMP_PROFILE,
        _ASSERTION_PROFILE,
        _EVENT_PROFILE,
        _JSON_PROFILE,
        _DATA_MANAGEMENT_PROFILE,
    )


def test_assertion_semantic_vectors_cover_schema_inexpressible_invariants() -> None:
    """Structural schema acceptance cannot bypass cross-field assertion rules."""
    profile = load_conformance_profile(_ASSERTION_PROFILE)
    validator = Draft202012Validator(
        load_schema("context-assertion.schema.json"),
        registry=_schema_registry(),
    )

    for vector in profile["invalid_vectors"]:
        value = vector["value"]
        assert list(validator.iter_errors(value)) == []
        with pytest.raises(ValueError, match=vector["error_pattern"]):
            ContextAssertion.from_mapping(value)


def _event(authority_uri, asset_uri, count: int) -> CloudEventEnvelope:
    """Build one valid CloudEvent around a conformance-profile integer."""
    return CloudEventEnvelope(
        event_id=UUID(EVENT_UUID7_TEXT),
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data={"nested": [{"count": count}]},
    )


def test_json_integer_profile_executes_at_installed_event_boundary(
    authority_uri,
    asset_uri,
) -> None:
    """Published integer vectors preserve exact values or fail closed."""
    profile = load_conformance_profile(_JSON_PROFILE)

    for value in profile["valid_integer_values"]:
        event = _event(authority_uri, asset_uri, value)
        assert event.to_mapping()["data"]["nested"][0]["count"] == value
    for value in profile["invalid_integer_values"]:
        with pytest.raises(ValueError, match="exact interoperable range"):
            _event(authority_uri, asset_uri, value)
