"""Regression tests for Context Assertion provenance invariants."""

from dataclasses import MISSING, fields
from typing import get_type_hints

from cwl_context_contracts import ContextAssertion, ProvenanceReference, TruthStatus
from cwl_context_contracts.schemas import load_schema
from cwl_context_contracts.truth import requires_provenance

_PROVENANCE_SCHEMA = (
    "https://schemas.contextualwisdomlab.org/context/"
    "provenance-reference.v1.schema.json"
)


def test_every_truth_disposition_requires_provenance() -> None:
    """Every cross-domain assertion retains evidence lineage for its disposition."""

    for status in TruthStatus:
        assert requires_provenance(status) is True


def test_context_assertion_schema_requires_non_null_provenance() -> None:
    """Published JSON Schema must not admit an assertion without provenance."""

    schema = load_schema("context-assertion.schema.json")

    assert "provenance" in schema["required"]
    assert schema["properties"]["provenance"] == {"$ref": _PROVENANCE_SCHEMA}


def test_python_sdk_requires_non_null_provenance_argument() -> None:
    """The typed Python surface must match the non-null published wire contract."""

    hints = get_type_hints(ContextAssertion)
    provenance_field = next(
        field for field in fields(ContextAssertion) if field.name == "provenance"
    )

    assert hints["provenance"] is ProvenanceReference
    assert provenance_field.default is MISSING
