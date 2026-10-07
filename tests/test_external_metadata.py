"""External metadata observation DTO, replay identity, and JSON boundary tests."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

import pytest

from cwl_context_contracts import (
    BitemporalInterval,
    CanonicalAssetUri,
    CanonicalAuthorityUri,
    ExternalEntityReference,
    ExternalMetadataLifecycle,
    ExternalMetadataSource,
    MetadataObservationEnvelope,
    ProvenanceReference,
    TruthStatus,
    derive_metadata_replay_id,
    parse_metadata_observation_json,
)

_OBSERVATION_UUID = "0195d145-64e8-7f4f-8a23-a0cc784cb711"
_SUPERSEDED_UUID = "0195d145-64e8-7f4f-8a23-a0cc784cb712"
_EVENT_UUID = "0195d145-64e8-7f4f-8a23-a0cc784cb799"
_SUBJECT_UUID = "0195d145-64e8-7f4f-8a23-a0cc784cb721"
_EVIDENCE_UUID = "0195d145-64e8-7f4f-8a23-a0cc784cb731"
_PAYLOAD_SHA256 = hashlib.sha256(b"cwl-authored metadata payload").hexdigest()
_NORMALIZED_SHA256 = hashlib.sha256(b"cwl-authored normalized payload").hexdigest()
_SCHEMA_SHA256 = hashlib.sha256(b"cwl-authored provider profile schema").hexdigest()
_EVIDENCE_SHA256 = hashlib.sha256(b"cwl-authored evidence bytes").hexdigest()


def _expected_replay_id(
    *,
    source_authority: str = "urn:cwl:tenant_001:metadata_bridge",
    tenant_id: str = "tenant_001",
    external_entity_type: str = "data_table",
    external_id: str = "f3b0c2a1-external-table-01",
    source_release: str = "provider-release-1.5.2",
    payload_sha256: str = _PAYLOAD_SHA256,
) -> str:
    """Compute the published replay digest independently of the SDK."""
    material = json.dumps(
        [
            "cwl-external-metadata-replay/v1",
            source_authority,
            tenant_id,
            external_entity_type,
            external_id,
            source_release,
            payload_sha256,
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _envelope_mapping() -> dict[str, Any]:
    """Return a CWL-authored foreign observation without vendor payload text."""
    return {
        "observation_id": (
            "urn:cwl:tenant_001:metadata_bridge:metadata_observation:"
            f"{_OBSERVATION_UUID}"
        ),
        "event_id": _EVENT_UUID,
        "source": {
            "source_authority": "urn:cwl:tenant_001:metadata_bridge",
            "provider_code": "openmetadata",
            "source_release": "provider-release-1.5.2",
            "schema_uri": "https://schemas.example.org/cwl-profile/table.v1.json",
            "schema_sha256": _SCHEMA_SHA256,
            "lifecycle": "active",
        },
        "entity": {
            "source_authority": "urn:cwl:tenant_001:metadata_bridge",
            "external_entity_type": "data_table",
            "external_id": "f3b0c2a1-external-table-01",
            "fully_qualified_name": "warehouse_service.sales_db.order_ledger",
        },
        "subject_ref": (
            f"urn:cwl:tenant_001:lineage_core:data_table:{_SUBJECT_UUID}"
        ),
        "truth_status": "observed",
        "interval": {
            "valid_from": "2026-10-01T00:00:00Z",
            "recorded_at": "2026-10-01T00:00:05Z",
            "valid_to": None,
            "superseded_at": None,
        },
        "provenance": {
            "evidence_ref": (
                "urn:cwl:tenant_001:metadata_bridge:metadata_evidence:"
                f"{_EVIDENCE_UUID}"
            ),
            "sha256": _EVIDENCE_SHA256,
            "source_locator": "metadata-export/order_ledger.json",
        },
        "payload_sha256": _PAYLOAD_SHA256,
        "normalized_sha256": _NORMALIZED_SHA256,
        "replay_id": _expected_replay_id(),
        "supersedes_observation_id": None,
    }


def test_foreign_observation_round_trips_without_rewriting_truth() -> None:
    """A parsed observation serializes back to the exact published wire shape."""
    value = _envelope_mapping()

    envelope = MetadataObservationEnvelope.from_mapping(value)

    assert envelope.to_mapping() == value
    assert envelope.truth_status is TruthStatus.OBSERVED
    assert type(envelope.source) is ExternalMetadataSource
    assert envelope.source.lifecycle is ExternalMetadataLifecycle.ACTIVE
    assert type(envelope.entity) is ExternalEntityReference
    assert type(envelope.interval) is BitemporalInterval
    assert type(envelope.provenance) is ProvenanceReference
    assert envelope.source.source_authority == CanonicalAuthorityUri.parse(
        "urn:cwl:tenant_001:metadata_bridge"
    )


@pytest.mark.parametrize("status", [status.value for status in TruthStatus])
def test_every_truth_status_round_trips_byte_identical(status: str) -> None:
    """The DTO retains each of the six statuses; it never ranks or maps them."""
    value = _envelope_mapping()
    value["truth_status"] = status

    assert MetadataObservationEnvelope.from_mapping(value).to_mapping() == value


def test_replay_identity_is_deterministic_and_matches_published_derivation() -> None:
    """Independent consumers derive the same replay identity from the same facts."""
    authority = CanonicalAuthorityUri.parse("urn:cwl:tenant_001:metadata_bridge")

    derived = derive_metadata_replay_id(
        source_authority=authority,
        external_entity_type="data_table",
        external_id="f3b0c2a1-external-table-01",
        source_release="provider-release-1.5.2",
        payload_sha256=_PAYLOAD_SHA256,
    )

    assert derived == _expected_replay_id()
    assert derived == derive_metadata_replay_id(
        source_authority=authority,
        external_entity_type="data_table",
        external_id="f3b0c2a1-external-table-01",
        source_release="provider-release-1.5.2",
        payload_sha256=_PAYLOAD_SHA256,
    )


def test_replay_identity_separates_tenants_payloads_and_field_framing() -> None:
    """Same external ID in another tenant, or changed bytes, never collide."""
    base = {
        "source_authority": CanonicalAuthorityUri.parse(
            "urn:cwl:tenant_001:metadata_bridge"
        ),
        "external_entity_type": "data_table",
        "external_id": "ab",
        "source_release": "c",
        "payload_sha256": _PAYLOAD_SHA256,
    }
    other_tenant = dict(
        base,
        source_authority=CanonicalAuthorityUri.parse(
            "urn:cwl:tenant_002:metadata_bridge"
        ),
    )
    changed_payload = dict(base, payload_sha256=_NORMALIZED_SHA256)
    reframed = dict(base, external_id="a", source_release="bc")

    identities = {
        derive_metadata_replay_id(**candidate)
        for candidate in (base, other_tenant, changed_payload, reframed)
    }

    assert len(identities) == 4


@pytest.mark.parametrize(
    ("keyword", "value", "error"),
    [
        ("source_authority", "urn:cwl:tenant_001:metadata_bridge", TypeError),
        ("external_entity_type", "DataTable", ValueError),
        ("external_id", "", ValueError),
        ("source_release", "release with spaces", ValueError),
        ("payload_sha256", _PAYLOAD_SHA256.upper(), ValueError),
    ],
)
def test_replay_derivation_rejects_unvalidated_inputs(
    keyword: str,
    value: object,
    error: type[Exception],
) -> None:
    """Replay identity is derived only from contract-valid components."""
    arguments: dict[str, Any] = {
        "source_authority": CanonicalAuthorityUri.parse(
            "urn:cwl:tenant_001:metadata_bridge"
        ),
        "external_entity_type": "data_table",
        "external_id": "external-01",
        "source_release": "provider-release-1",
        "payload_sha256": _PAYLOAD_SHA256,
    }
    arguments[keyword] = value

    with pytest.raises(error):
        derive_metadata_replay_id(**arguments)


def _mutated(path: tuple[str, ...], value: object) -> dict[str, Any]:
    """Return the valid mapping with one nested member replaced."""
    mapping = deepcopy(_envelope_mapping())
    target: dict[str, Any] = mapping
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return mapping


def _without(path: tuple[str, ...]) -> dict[str, Any]:
    """Return the valid mapping with one nested member removed."""
    mapping = deepcopy(_envelope_mapping())
    target: dict[str, Any] = mapping
    for key in path[:-1]:
        target = target[key]
    del target[path[-1]]
    return mapping


@pytest.mark.parametrize(
    ("value", "error", "pattern"),
    [
        (_mutated(("provenance",), None), ValueError, "provenance is required"),
        (_without(("provenance",)), ValueError, "missing required"),
        (_mutated(("truth_status",), "Observed"), ValueError, "unknown truth"),
        (_mutated(("truth_status",), "confirmed"), ValueError, "unknown truth"),
        (_mutated(("truth_status",), True), TypeError, "truth_status"),
        (_mutated(("event_id",), _EVENT_UUID.upper()), ValueError, "canonical"),
        (
            _mutated(("event_id",), "0195d145-64e8-4f4f-8a23-a0cc784cb799"),
            ValueError,
            "UUIDv7",
        ),
        (_mutated(("event_id",), 7), TypeError, "event_id"),
        (_mutated(("rogue_field",), "x"), ValueError, "unknown metadata observation"),
        (
            _mutated(("source", "rogue_field"), "x"),
            ValueError,
            "unknown external metadata source",
        ),
        (
            _mutated(("entity", "rogue_field"), "x"),
            ValueError,
            "unknown external entity",
        ),
        (_without(("source", "schema_sha256")), ValueError, "missing required"),
        (_without(("entity", "external_id")), ValueError, "missing required"),
        (_mutated(("source",), []), TypeError, "source must be a mapping"),
        (_mutated(("entity",), "entity"), TypeError, "entity must be a mapping"),
        (
            _mutated(("source", "source_authority"), "urn:cwl:Tenant_001:bridge"),
            ValueError,
            "authority URI",
        ),
        (
            _mutated(("source", "source_authority"), "urn:cwl:tenant_001:bridge\n"),
            ValueError,
            "authority URI",
        ),
        (
            _mutated(("source", "source_authority"), "urn:cwl:tеnant_001:bridge"),
            ValueError,
            "authority URI",
        ),
        (
            _mutated(("source", "provider_code"), "OpenMetadata"),
            ValueError,
            "provider_code",
        ),
        (
            _mutated(("source", "provider_code"), "p" * 64),
            ValueError,
            "provider_code",
        ),
        (_mutated(("source", "source_release"), ""), ValueError, "source_release"),
        (
            _mutated(("source", "source_release"), "r" * 129),
            ValueError,
            "source_release",
        ),
        (_mutated(("source", "source_release"), 152), TypeError, "source_release"),
        (
            _mutated(("source", "schema_uri"), "http://schemas.example.org/a.json"),
            ValueError,
            "schema_uri",
        ),
        (
            _mutated(("source", "schema_uri"), "https://"),
            ValueError,
            "schema_uri",
        ),
        (
            _mutated(("source", "schema_uri"), "https://example.org/a b"),
            ValueError,
            "schema_uri",
        ),
        (
            _mutated(
                ("source", "schema_uri"),
                "https://example.org/" + "a" * 2048,
            ),
            ValueError,
            "schema_uri",
        ),
        (
            _mutated(("source", "schema_sha256"), "sha256:" + _SCHEMA_SHA256[7:]),
            ValueError,
            "schema_sha256",
        ),
        (_mutated(("source", "lifecycle"), "Active"), ValueError, "lifecycle"),
        (_mutated(("source", "lifecycle"), 1), TypeError, "lifecycle"),
        (_mutated(("entity", "external_id"), ""), ValueError, "external_id"),
        (_mutated(("entity", "external_id"), "x" * 513), ValueError, "external_id"),
        (_mutated(("entity", "external_id"), "id\x00null"), ValueError, "external_id"),
        (_mutated(("entity", "external_id"), "id\ud800"), ValueError, "external_id"),
        (_mutated(("entity", "external_id"), 12345), TypeError, "external_id"),
        (
            _mutated(("entity", "fully_qualified_name"), "f" * 1025),
            ValueError,
            "fully_qualified_name",
        ),
        (
            _mutated(("entity", "fully_qualified_name"), "line\nbreak"),
            ValueError,
            "fully_qualified_name",
        ),
        (
            _mutated(("entity", "external_entity_type"), "Table"),
            ValueError,
            "external_entity_type",
        ),
        (
            _mutated(("payload_sha256",), _PAYLOAD_SHA256[:63]),
            ValueError,
            "payload_sha256",
        ),
        (
            _mutated(("normalized_sha256",), _NORMALIZED_SHA256 + "0"),
            ValueError,
            "normalized_sha256",
        ),
        (_mutated(("replay_id",), None), TypeError, "replay_id"),
        (
            _mutated(
                ("observation_id",),
                "urn:cwl:tenant_001:metadata_bridge:data_table:"
                f"{_OBSERVATION_UUID}",
            ),
            ValueError,
            "metadata_observation",
        ),
        (
            _mutated(
                ("supersedes_observation_id",),
                "urn:cwl:tenant_001:metadata_bridge:data_table:"
                f"{_SUPERSEDED_UUID}",
            ),
            ValueError,
            "metadata_observation",
        ),
        (
            _mutated(("interval", "valid_to"), "2026-09-30T00:00:00Z"),
            ValueError,
            "valid_to",
        ),
        (
            _mutated(("interval", "superseded_at"), "2026-10-01T00:00:04Z"),
            ValueError,
            "superseded_at",
        ),
        (
            _mutated(("interval", "valid_from"), "2026-10-01T00:00:00"),
            ValueError,
            "CWL timestamp",
        ),
        (
            _mutated(("interval", "valid_to"), "2026-12-31T23:59:60Z"),
            ValueError,
            "CWL timestamp",
        ),
        ("not a mapping", TypeError, "value must be a mapping"),
    ],
)
def test_hostile_observation_mappings_fail_closed(
    value: object,
    error: type[Exception],
    pattern: str,
) -> None:
    """Every malformed or ambiguous observation is rejected before admission."""
    with pytest.raises(error, match=pattern):
        MetadataObservationEnvelope.from_mapping(value)  # type: ignore[arg-type]


def test_retroactive_and_prospective_recording_remain_valid() -> None:
    """Recording before validity starts is legal bitemporal history."""
    value = _mutated(("interval", "recorded_at"), "2026-09-01T00:00:00Z")

    assert MetadataObservationEnvelope.from_mapping(value).to_mapping() == value


def test_supersession_reference_is_carried_as_a_new_fact() -> None:
    """A superseding observation references the prior fact by identity only."""
    value = _mutated(
        ("supersedes_observation_id",),
        f"urn:cwl:tenant_001:metadata_bridge:metadata_observation:{_SUPERSEDED_UUID}",
    )

    envelope = MetadataObservationEnvelope.from_mapping(value)

    assert envelope.supersedes_observation_id == CanonicalAssetUri.parse(
        value["supersedes_observation_id"]
    )
    assert envelope.to_mapping() == value


def test_absent_supersession_reference_is_an_open_optional_field() -> None:
    """Omitting the optional supersession member equals an explicit null."""
    value = _without(("supersedes_observation_id",))

    envelope = MetadataObservationEnvelope.from_mapping(value)

    assert envelope.supersedes_observation_id is None
    assert envelope.to_mapping() == _envelope_mapping()


def test_direct_construction_rejects_untyped_components() -> None:
    """SDK callers cannot bypass parsing with loosely typed nested values."""
    envelope = MetadataObservationEnvelope.from_mapping(_envelope_mapping())
    replacements: dict[str, object] = {
        "observation_id": str(envelope.observation_id),
        "source": envelope.source.to_mapping(),
        "entity": envelope.entity.to_mapping(),
        "subject_ref": str(envelope.subject_ref),
        "interval": envelope.interval.to_mapping(),
        "provenance": envelope.provenance.to_mapping(),
        "supersedes_observation_id": str(envelope.observation_id),
    }
    for field_name, replacement in replacements.items():
        arguments = {
            name: getattr(envelope, name)
            for name in MetadataObservationEnvelope.__dataclass_fields__
        }
        arguments[field_name] = replacement
        with pytest.raises(TypeError, match=field_name):
            MetadataObservationEnvelope(**arguments)


def test_component_dtos_reject_untyped_authorities() -> None:
    """Source and entity DTOs require parsed authority identities."""
    with pytest.raises(TypeError, match="source_authority"):
        ExternalMetadataSource(
            source_authority="urn:cwl:tenant_001:metadata_bridge",  # type: ignore[arg-type]
            provider_code="openmetadata",
            source_release="r1",
            schema_uri="https://schemas.example.org/a.json",
            schema_sha256=_SCHEMA_SHA256,
            lifecycle=ExternalMetadataLifecycle.ACTIVE,
        )
    with pytest.raises(TypeError, match="source_authority"):
        ExternalEntityReference(
            source_authority="urn:cwl:tenant_001:metadata_bridge",  # type: ignore[arg-type]
            external_entity_type="data_table",
            external_id="external-01",
            fully_qualified_name="warehouse_service.sales_db.order_ledger",
        )


def test_json_parser_accepts_one_strict_observation_document() -> None:
    """The text boundary returns the same envelope as the mapping boundary."""
    text = json.dumps(_envelope_mapping())

    envelope = parse_metadata_observation_json(text)

    assert envelope == MetadataObservationEnvelope.from_mapping(_envelope_mapping())


@pytest.mark.parametrize(
    ("text", "pattern"),
    [
        (
            '{"truth_status":"observed","truth_status":"authoritative"}',
            "duplicate JSON object member",
        ),
        (
            '{"provenance":{"sha256":"a","sha256":"b"}}',
            "duplicate JSON object member",
        ),
        ('{"normalized_sha256": NaN}', "non-standard JSON constant"),
        ('{"normalized_sha256": Infinity}', "non-standard JSON constant"),
        ('{"normalized_sha256": -Infinity}', "non-standard JSON constant"),
        ('{"source_release": 9007199254740992}', "exact interoperable range"),
        ("[" * 70 + "]" * 70, "JSON nesting depth"),
        ("[]", "JSON object"),
        ('"\\ud800"', "metadata observation JSON must contain Unicode scalar values"),
        ("{", "malformed"),
        ('"valid"', "JSON object"),
        (" " * 65537, "exceeds 65536 bytes"),
        ("{}\ud800", "valid Unicode"),
    ],
)
def test_json_parser_rejects_hostile_text(text: str, pattern: str) -> None:
    """Ambiguous, non-finite, oversize, or non-object JSON never reaches the DTO."""
    with pytest.raises(ValueError, match=pattern):
        parse_metadata_observation_json(text)


def test_json_parser_requires_text() -> None:
    """Bytes must be decoded by the transport before contract parsing."""
    with pytest.raises(TypeError, match="must be a string"):
        parse_metadata_observation_json(b"{}")  # type: ignore[arg-type]
