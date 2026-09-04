"""Provider-neutral CloudEvent semantic conformance regressions."""

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from cwl_context_contracts import (
    CloudEventEnvelope,
    available_schema_names,
    load_conformance_profile,
    load_schema,
)

_EVENT_PROFILE = "cloudevent-semantics.v1.json"


def _schema_registry() -> Registry:
    """Return every packaged schema as one Draft 2020-12 registry."""

    schemas = [load_schema(name) for name in available_schema_names()]
    return Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )


def test_event_semantic_profile_closes_default_schema_annotation_gaps() -> None:
    """Installed consumers must reject event invariants structural JSON cannot prove."""

    profile = load_conformance_profile(_EVENT_PROFILE)
    validator = Draft202012Validator(
        load_schema("cloudevent-envelope.schema.json"),
        registry=_schema_registry(),
    )

    for vector in profile["invalid_vectors"]:
        value = vector["value"]
        assert list(validator.iter_errors(value)) == []
        with pytest.raises(ValueError, match=vector["error_pattern"]):
            CloudEventEnvelope.from_mapping(value)

    for vector in profile["valid_vectors"]:
        value = vector["value"]
        assert list(validator.iter_errors(value)) == []
        assert CloudEventEnvelope.from_mapping(value).to_mapping() == value
