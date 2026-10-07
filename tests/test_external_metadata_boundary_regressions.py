"""Decoded Unicode regressions for the new metadata JSON boundary only."""

from __future__ import annotations

import json
from typing import Any

import pytest

from cwl_context_contracts import (
    admit_metadata_observation,
    load_fixture,
    parse_metadata_observation_json,
)
from tests.test_external_metadata import _expected_replay_id


@pytest.mark.parametrize("surrogate", ["\ud800", "\udbff", "\udc00", "\udfff"])
@pytest.mark.parametrize(
    "location", ["locator", "external_id", "nested_key", "nested_list", "root_string"]
)
def test_decoded_surrogates_fail_before_contract_fields(
    surrogate: str, location: str
) -> None:
    """Escaped non-scalars in any decoded string or key fail at the boundary."""
    value: Any = load_fixture("metadata-observation-envelope.valid.json")
    if location == "locator":
        value["provenance"]["source_locator"] = "synthetic-" + surrogate + "-locator"
    elif location == "external_id":
        value["entity"]["external_id"] = "external-" + surrogate
    elif location == "nested_key":
        value["provenance"]["extra"] = {"nested-" + surrogate: "value"}
    elif location == "nested_list":
        value["provenance"]["extra"] = [{"nested": ["value-" + surrogate]}]
    else:
        value = surrogate

    text = json.dumps(value, ensure_ascii=True)
    assert text.isascii()
    with pytest.raises(
        ValueError,
        match="^metadata observation JSON must contain Unicode scalar values$",
    ):
        admit_metadata_observation(parse_metadata_observation_json(text))


@pytest.mark.parametrize(
    "identifier", ["external-\U0001f600", "caf\u00e9", "cafe\u0301"]
)
@pytest.mark.parametrize("ensure_ascii", [True, False])
def test_unicode_scalar_controls_round_trip_without_normalization(
    identifier: str, ensure_ascii: bool
) -> None:
    """Astral escapes and literal NFC/NFD retain exact identity and receipt text."""
    value = load_fixture("metadata-observation-envelope.valid.json")
    value["entity"]["external_id"] = identifier
    value["entity"]["fully_qualified_name"] = "warehouse_service.sales_db." + identifier
    value["provenance"]["source_locator"] = "synthetic/" + identifier
    value["replay_id"] = _expected_replay_id(external_id=identifier)

    envelope = parse_metadata_observation_json(
        json.dumps(value, ensure_ascii=ensure_ascii)
    )
    assert envelope.to_mapping() == value
    receipt = admit_metadata_observation(envelope)
    assert receipt.result.value == "admitted"
    assert receipt.to_mapping()["external_id"] == identifier
    assert (
        receipt.to_mapping()["provenance"]["source_locator"]
        == "synthetic/" + identifier
    )
    json.dumps(receipt.to_mapping(), ensure_ascii=False).encode("utf-8")


def test_nfc_and_nfd_remain_distinct_replay_identities() -> None:
    """Canonically equivalent opaque IDs must not be silently normalized."""
    identities = []
    for identifier in ("caf\u00e9", "cafe\u0301"):
        value = load_fixture("metadata-observation-envelope.valid.json")
        value["entity"]["external_id"] = identifier
        value["replay_id"] = _expected_replay_id(external_id=identifier)
        envelope = parse_metadata_observation_json(json.dumps(value))
        assert envelope.entity.external_id == identifier
        identities.append(admit_metadata_observation(envelope).to_mapping()["replay_id"])
    assert identities[0] != identities[1]


@pytest.mark.parametrize("value", [{"\U0001f600": ["caf\u00e9", "cafe\u0301"]}])
def test_valid_nested_unicode_reaches_contract_validation(value: object) -> None:
    """Unicode scalar keys and lists are accepted before unknown-field rejection."""
    mapping = load_fixture("metadata-observation-envelope.valid.json")
    mapping["extra"] = value
    with pytest.raises(ValueError, match="unknown metadata observation fields"):
        parse_metadata_observation_json(json.dumps(mapping))


@pytest.mark.parametrize("depth", [70, 1000, 30000])
def test_deep_json_is_rejected_with_value_error(depth: int) -> None:
    """Below-cap deep wire arrays fail with ValueError on supported decoders."""
    text = "[" * depth + "0" + "]" * depth
    assert len(text.encode("utf-8")) < 65536
    with pytest.raises(ValueError, match="JSON nesting depth"):
        parse_metadata_observation_json(text)


def test_decoder_recursion_error_is_sanitized(monkeypatch: pytest.MonkeyPatch) -> None:
    """A decoder recursion failure has the same bounded parser error contract."""
    import cwl_context_contracts.external_metadata as external_metadata

    def raise_recursion_error(*args: object, **kwargs: object) -> object:
        raise RecursionError("synthetic decoder depth")

    monkeypatch.setattr(external_metadata.json, "loads", raise_recursion_error)
    with pytest.raises(ValueError, match="nesting is too deep"):
        parse_metadata_observation_json("{}")
