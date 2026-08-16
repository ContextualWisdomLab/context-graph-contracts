"""AsyncAPI component-contract regressions."""

import pytest

from cwl_context_contracts import available_contract_names, load_contract


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
        "schemaFormat": "application/schema+json;version=draft-2020-12",
        "schema": {
            "$ref": (
                "https://schemas.contextualwisdomlab.org/context/"
                "cloudevent-envelope.v1.schema.json"
            )
        },
    }


def test_unknown_asyncapi_contract_is_rejected() -> None:
    """Resource lookup fails closed for names outside the package inventory."""
    with pytest.raises(ValueError, match="unknown contract name"):
        load_contract("missing.asyncapi.json")
