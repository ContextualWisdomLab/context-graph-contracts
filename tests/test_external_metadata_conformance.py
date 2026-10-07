"""Packaged schema, fixture, and conformance surfaces for metadata observations."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

import cwl_context_contracts.conformance_runner as runner
from cwl_context_contracts import (
    MetadataObservationEnvelope,
    admit_metadata_observation,
    available_conformance_profile_names,
    available_fixture_names,
    available_schema_names,
    load_conformance_profile,
    load_fixture,
    load_schema,
    run_packaged_conformance,
)
from tests.conftest import RFC3339_FORMAT_CHECKER

_PROFILE_NAME = "external-metadata-observation-semantics.v1.json"
_ENVELOPE_SCHEMA = "metadata-observation-envelope.schema.json"
_RECEIPT_SCHEMA = "metadata-projection-receipt.schema.json"
_SOURCE_SCHEMA = "external-metadata-source.schema.json"
_ENTITY_SCHEMA = "external-entity-reference.schema.json"
_VALID_FIXTURE = "metadata-observation-envelope.valid.json"
_INVALID_FIXTURE = "metadata-observation-envelope.invalid.json"
_RECEIPT_FIXTURE = "metadata-projection-receipt.valid.json"


def _validator(schema_name: str) -> Draft202012Validator:
    """Return a Draft 2020-12 validator with every packaged schema registered."""
    schemas = [load_schema(name) for name in available_schema_names()]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    return Draft202012Validator(
        load_schema(schema_name),
        registry=registry,
        format_checker=RFC3339_FORMAT_CHECKER,
    )


def test_new_resources_are_appended_without_reordering_existing_inventory() -> None:
    """Existing manifests keep their order; new resources are strictly appended."""
    assert available_schema_names()[-4:] == (
        _SOURCE_SCHEMA,
        _ENTITY_SCHEMA,
        _ENVELOPE_SCHEMA,
        _RECEIPT_SCHEMA,
    )
    assert available_fixture_names()[-3:] == (
        _VALID_FIXTURE,
        _INVALID_FIXTURE,
        _RECEIPT_FIXTURE,
    )
    assert available_conformance_profile_names()[-1] == _PROFILE_NAME


def test_schemas_are_draft_2020_12_and_closed_to_unknown_members() -> None:
    """Every new object schema is a closed Draft 2020-12 contract."""
    for name in (_SOURCE_SCHEMA, _ENTITY_SCHEMA, _ENVELOPE_SCHEMA, _RECEIPT_SCHEMA):
        schema = load_schema(name)
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"] == (
            "https://schemas.contextualwisdomlab.org/context/"
            f"{name.removesuffix('.schema.json')}.v1.schema.json"
        )
        assert schema["additionalProperties"] is False


def test_positive_fixtures_satisfy_schema_and_sdk() -> None:
    """Packaged positive fixtures pass structural and semantic validation."""
    envelope = load_fixture(_VALID_FIXTURE)
    receipt = load_fixture(_RECEIPT_FIXTURE)

    _validator(_ENVELOPE_SCHEMA).validate(envelope)
    _validator(_RECEIPT_SCHEMA).validate(receipt)
    _validator(_SOURCE_SCHEMA).validate(envelope["source"])
    _validator(_ENTITY_SCHEMA).validate(envelope["entity"])
    assert MetadataObservationEnvelope.from_mapping(envelope).to_mapping() == envelope
    assert admit_metadata_observation(envelope).to_mapping() == receipt


def test_negative_fixture_is_rejected_by_schema_and_sdk() -> None:
    """The packaged negative fixture fails both structural and SDK validation."""
    invalid = load_fixture(_INVALID_FIXTURE)

    assert not _validator(_ENVELOPE_SCHEMA).is_valid(invalid)
    with pytest.raises(ValueError, match="provenance is required"):
        MetadataObservationEnvelope.from_mapping(invalid)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("vendor_payload",), {}),
        (("truth_status",), "confirmed"),
        (("source", "provider_code"), "OpenMetadata"),
        (("source", "schema_uri"), "http://schemas.example.org/a.json"),
        (("source", "schema_sha256"), "A" * 64),
        (("entity", "external_id"), ""),
        (("entity", "rogue_field"), "x"),
        (("payload_sha256",), "sha256:abc"),
        (("event_id",), "0195D145-64E8-7F4F-8A23-A0CC784CB799"),
        (("interval", "valid_from"), "2026-10-01"),
        (("provenance",), None),
    ],
)
def test_envelope_schema_rejects_structural_hostile_values(
    path: tuple[str, ...],
    value: object,
) -> None:
    """Schema-only consumers still reject structurally invalid observations."""
    candidate: dict[str, Any] = deepcopy(load_fixture(_VALID_FIXTURE))
    target = candidate
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    assert not _validator(_ENVELOPE_SCHEMA).is_valid(candidate)


@pytest.mark.parametrize(
    ("member", "value"),
    [
        ("result", "accepted"),
        ("reason_code", "trusted_provider"),
        ("profile_version", True),
        ("contract_version", "1"),
        ("vendor_payload", {}),
    ],
)
def test_receipt_schema_rejects_unbounded_values(member: str, value: object) -> None:
    """Receipt consumers can rely on a closed result and reason vocabulary."""
    candidate = deepcopy(load_fixture(_RECEIPT_FIXTURE))
    candidate[member] = value

    assert not _validator(_RECEIPT_SCHEMA).is_valid(candidate)


def test_profile_covers_every_required_hostile_case() -> None:
    """Non-Python consumers receive the hostile regression corpus by case ID."""
    profile = load_conformance_profile(_PROFILE_NAME)
    case_ids = {
        str(vector["case_id"])
        for key in (
            "valid_vectors",
            "rejected_vectors",
            "invalid_vectors",
            "invalid_json_texts",
            "replay_vectors",
        )
        for vector in profile[key]
    }

    assert {
        "foreign_authoritative_promotion",
        "foreign_superseded_forgery",
        "foreign_rejected_forgery",
        "missing_provenance",
        "cross_tenant_subject",
        "entity_source_mismatch",
        "duplicate_truth_status_member",
        "nan_literal",
        "changed_payload_reuses_replay_id",
        "other_tenant_same_external_id",
        "supersession_as_new_fact",
        "retroactive_recording_is_valid",
    } <= case_ids


def test_profile_vectors_execute_through_the_packaged_runner() -> None:
    """Every profile vector is executed and counted by the buyer-facing runner."""
    profile = load_conformance_profile(_PROFILE_NAME)
    expected = sum(
        len(profile[key])
        for key in (
            "valid_vectors",
            "rejected_vectors",
            "invalid_vectors",
            "invalid_json_texts",
            "replay_vectors",
        )
    )

    case_count, failures = runner._run_external_metadata_observation_profile(
        _PROFILE_NAME,
        profile,
    )

    assert failures == ()
    assert case_count == expected
    assert run_packaged_conformance().passed is True


def _drift(profile: dict[str, Any], key: str, vector: dict[str, Any]) -> None:
    """Replace every vector list with one drifted vector under ``key``."""
    for name in (
        "valid_vectors",
        "rejected_vectors",
        "invalid_vectors",
        "invalid_json_texts",
        "replay_vectors",
    ):
        profile[name] = []
    profile[key] = [vector]


@pytest.mark.parametrize(
    ("key", "mutation", "detail"),
    [
        (
            "valid_vectors",
            {"expected_reason_code": "admitted_owner_disposition"},
            "reason",
        ),
        (
            "valid_vectors",
            {"value": {"truth_status": "observed"}},
            "unexpectedly rejected",
        ),
        (
            "rejected_vectors",
            {"expected_reason_code": "tenant_scope_mismatch"},
            "reason",
        ),
        ("invalid_vectors", {"value": None}, "unexpectedly accepted"),
        ("invalid_json_texts", {}, "unexpectedly accepted"),
        ("replay_vectors", {"expected_replay_id": "0" * 64}, "replay"),
        (
            "replay_vectors",
            {"source_authority": "urn:cwl:Tenant:bridge"},
            "replay vector was unexpectedly rejected",
        ),
    ],
)
def test_runner_reports_each_kind_of_profile_drift(
    key: str,
    mutation: dict[str, Any],
    detail: str,
) -> None:
    """Drift in any vector family is reported with its exact case identity."""
    profile = load_conformance_profile(_PROFILE_NAME)
    if key == "invalid_vectors":
        vector = {
            "case_id": "drifted",
            "error_pattern": "never",
            "value": load_fixture(_VALID_FIXTURE),
        }
    elif key == "invalid_json_texts":
        vector = {
            "case_id": "drifted",
            "error_pattern": "never",
            "text": json.dumps(load_fixture(_VALID_FIXTURE)),
        }
    else:
        vector = deepcopy(profile[key][0])
        vector["case_id"] = "drifted"
        vector.update(mutation)
    _drift(profile, key, vector)

    _, failures = runner._run_external_metadata_observation_profile(
        _PROFILE_NAME,
        profile,
    )

    assert [failure.case_id for failure in failures] == ["drifted"]
    assert detail in failures[0].detail


def test_runner_rejects_profile_identity_drift() -> None:
    """A renamed or re-versioned profile cannot be executed as this contract."""
    profile = load_conformance_profile(_PROFILE_NAME)
    profile["profile_version"] = 2

    _, failures = runner._run_external_metadata_observation_profile(
        _PROFILE_NAME,
        profile,
    )

    assert [failure.case_id for failure in failures] == ["profile_identity"]
