"""AsyncAPI component-contract regressions."""

import pytest

from cwl_context_contracts import available_contract_names, load_contract
from cwl_context_contracts.assertion import ASSERTION_EVENT_TYPE


_SCHEMA_FORMAT = "application/schema+json;version=draft-2020-12"
_SCHEMA_ROOT = "https://schemas.contextualwisdomlab.org/context/"


def test_packaged_asyncapi_contract_is_provider_neutral() -> None:
    """The shared AsyncAPI document exposes message components without topology."""
    assert available_contract_names() == ("context-fabric.asyncapi.json",)

    document = load_contract("context-fabric.asyncapi.json")

    assert document["asyncapi"] == "3.1.0"
    assert document["id"] == "urn:cwl:shared:context_graph_contracts"
    assert "servers" not in document
    assert "channels" not in document
    assert "operations" not in document

    message = document["components"]["messages"]["ContextGraphCloudEvent"]
    assert message["contentType"] == "application/cloudevents+json"
    assert message["payload"] == {
        "schemaFormat": _SCHEMA_FORMAT,
        "schema": {"$ref": f"{_SCHEMA_ROOT}cloudevent-envelope.v1.schema.json"},
    }


def test_context_assertion_message_is_a_structured_cloudevent() -> None:
    """Assertion events wrap assertion data instead of mislabelling bare data as CE JSON."""

    document = load_contract("context-fabric.asyncapi.json")
    message = document["components"]["messages"]["ContextAssertionEvent"]

    assert message["contentType"] == "application/cloudevents+json"
    assert message["payload"]["schemaFormat"] == _SCHEMA_FORMAT
    assert message["payload"]["schema"] == {
        "allOf": [
            {"$ref": f"{_SCHEMA_ROOT}cloudevent-envelope.v1.schema.json"},
            {
                "type": "object",
                "required": ["type", "dataschema", "data"],
                "properties": {
                    "type": {"const": ASSERTION_EVENT_TYPE},
                    "dataschema": {
                        "const": f"{_SCHEMA_ROOT}context-assertion.v1.schema.json"
                    },
                    "data": {
                        "$ref": f"{_SCHEMA_ROOT}context-assertion.v1.schema.json"
                    },
                },
            },
        ]
    }


def test_unknown_asyncapi_contract_is_rejected() -> None:
    """Resource lookup fails closed for names outside the package inventory."""
    with pytest.raises(ValueError, match="unknown contract name"):
        load_contract("missing.asyncapi.json")
