"""Wire-level provenance requirements for Context Assertion interchange."""

from dataclasses import replace

import pytest

from cwl_context_contracts import ContextAssertion, TruthStatus, load_fixture, load_schema


def test_context_assertion_wire_requires_provenance_for_every_truth_status() -> None:
    """No truth disposition may cross a Context Fabric boundary without provenance."""

    fixture = load_fixture("valid-assertion.json")
    for status in TruthStatus:
        missing = {**fixture, "truth_status": status.value}
        missing.pop("provenance", None)
        with pytest.raises(ValueError, match="provenance"):
            ContextAssertion.from_mapping(missing)

        null_provenance = {
            **fixture,
            "truth_status": status.value,
            "provenance": None,
        }
        with pytest.raises(ValueError, match="provenance"):
            ContextAssertion.from_mapping(null_provenance)


def test_context_assertion_serializer_refuses_provenance_free_local_value() -> None:
    """An internal value without evidence cannot be serialized onto the shared wire."""

    parsed = ContextAssertion.from_mapping(load_fixture("valid-assertion.json"))
    local_only = replace(
        parsed,
        truth_status=TruthStatus.INFERRED,
        provenance=None,
    )
    with pytest.raises(ValueError, match="provenance"):
        local_only.to_mapping()


def test_context_assertion_schema_requires_non_null_provenance() -> None:
    """The published v1 schema must fail closed before consumer projection."""

    schema = load_schema("context-assertion.schema.json")
    assert "provenance" in schema["required"]
    assert schema["properties"]["provenance"] == {
        "$ref": "https://schemas.contextualwisdomlab.org/context/provenance-reference.v1.schema.json"
    }
