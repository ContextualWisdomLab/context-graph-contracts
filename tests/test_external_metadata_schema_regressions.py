"""Canonical schema regressions for lexical closure and Unicode scalars."""

from __future__ import annotations

from copy import deepcopy

import pytest

from cwl_context_contracts import load_fixture
from tests.test_external_metadata_conformance import (
    _ENTITY_SCHEMA,
    _ENVELOPE_SCHEMA,
    _RECEIPT_SCHEMA,
    _SOURCE_SCHEMA,
    _validator,
)


@pytest.mark.parametrize(
    ("schema_name", "fixture_name", "path"),
    [
        (
            _SOURCE_SCHEMA,
            "metadata-observation-envelope.valid.json",
            ("source", "provider_code"),
        ),
        (
            _SOURCE_SCHEMA,
            "metadata-observation-envelope.valid.json",
            ("source", "source_release"),
        ),
        (
            _SOURCE_SCHEMA,
            "metadata-observation-envelope.valid.json",
            ("source", "schema_uri"),
        ),
        (
            _ENTITY_SCHEMA,
            "metadata-observation-envelope.valid.json",
            ("entity", "external_entity_type"),
        ),
        (
            _ENTITY_SCHEMA,
            "metadata-observation-envelope.valid.json",
            ("entity", "external_id"),
        ),
        (
            _ENTITY_SCHEMA,
            "metadata-observation-envelope.valid.json",
            ("entity", "fully_qualified_name"),
        ),
        (_ENVELOPE_SCHEMA, "metadata-observation-envelope.valid.json", ("event_id",)),
        (
            _ENVELOPE_SCHEMA,
            "metadata-observation-envelope.valid.json",
            ("payload_sha256",),
        ),
        (
            _RECEIPT_SCHEMA,
            "metadata-projection-receipt.valid.json",
            ("provider_code",),
        ),
        (
            _RECEIPT_SCHEMA,
            "metadata-projection-receipt.valid.json",
            ("source_release",),
        ),
        (
            _RECEIPT_SCHEMA,
            "metadata-projection-receipt.valid.json",
            ("external_entity_type",),
        ),
        (_RECEIPT_SCHEMA, "metadata-projection-receipt.valid.json", ("external_id",)),
        (_RECEIPT_SCHEMA, "metadata-projection-receipt.valid.json", ("event_id",)),
        (_RECEIPT_SCHEMA, "metadata-projection-receipt.valid.json", ("replay_id",)),
        (
            _RECEIPT_SCHEMA,
            "metadata-projection-receipt.valid.json",
            ("contract_version",),
        ),
    ],
)
def test_new_schemas_reject_final_lf_where_python_rejects(
    schema_name: str, fixture_name: str, path: tuple[str, ...]
) -> None:
    """New schema lexical constraints are absolute at the end of each token."""
    candidate = deepcopy(load_fixture(fixture_name))
    target = candidate
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] += "\n"

    assert not _validator(schema_name).is_valid(candidate)


def test_schema_uri_accepts_valid_path_query_and_fragment() -> None:
    """The schema URI pattern matches the SDK's HTTPS URI surface."""
    source = deepcopy(load_fixture("metadata-observation-envelope.valid.json"))[
        "source"
    ]
    source["schema_uri"] = (
        "https://schemas.example.org/cwl-profile/table.v1.json?x=1#fragment"
    )

    assert _validator(_SOURCE_SCHEMA).is_valid(source)


def test_schema_uri_rejects_missing_host() -> None:
    """The structural schema requires a non-empty HTTPS host like the SDK."""
    source = deepcopy(load_fixture("metadata-observation-envelope.valid.json"))[
        "source"
    ]
    source["schema_uri"] = "https:///foo"

    assert not _validator(_SOURCE_SCHEMA).is_valid(source)


def test_all_new_schema_surfaces_accept_valid_non_bmp_unicode() -> None:
    """Entity, envelope, source, and receipt schemas preserve scalar Unicode."""
    envelope = deepcopy(load_fixture("metadata-observation-envelope.valid.json"))
    identifier = "external-\U0001f600"
    envelope["entity"]["external_id"] = identifier
    envelope["entity"]["fully_qualified_name"] = (
        "warehouse_service.sales_db." + identifier
    )
    envelope["provenance"]["source_locator"] = "metadata-export/" + identifier
    source = envelope["source"]
    entity = envelope["entity"]
    receipt = deepcopy(load_fixture("metadata-projection-receipt.valid.json"))
    receipt["external_id"] = identifier
    receipt["provenance"]["source_locator"] = "metadata-export/" + identifier

    assert _validator(_SOURCE_SCHEMA).is_valid(source)
    assert _validator(_ENTITY_SCHEMA).is_valid(entity)
    assert _validator(_ENVELOPE_SCHEMA).is_valid(envelope)
    assert _validator(_RECEIPT_SCHEMA).is_valid(receipt)
