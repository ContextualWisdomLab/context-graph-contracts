"""Admission and receipt semantics for external metadata observations."""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest

import cwl_context_contracts.external_metadata_admission as admission_module
from cwl_context_contracts import (
    METADATA_RECEIPT_REASON_CODES,
    MetadataAdmissionResult,
    MetadataObservationEnvelope,
    MetadataProjectionReceipt,
    admit_metadata_observation,
)
from tests.test_external_metadata import (
    _OBSERVATION_UUID,
    _SUBJECT_UUID,
    _envelope_mapping,
    _expected_replay_id,
    _mutated,
)

_OWNER_AUTHORITY = "urn:cwl:tenant_001:lineage_core"
_FOREIGN_AUTHORITY = "urn:cwl:tenant_001:metadata_bridge"


def _owner_mapping(status: str) -> dict[str, Any]:
    """Return an observation whose source authority owns the subject."""
    value = _envelope_mapping()
    value["truth_status"] = status
    value["source"]["source_authority"] = _OWNER_AUTHORITY
    value["entity"]["source_authority"] = _OWNER_AUTHORITY
    value["observation_id"] = (
        f"{_OWNER_AUTHORITY}:metadata_observation:{_OBSERVATION_UUID}"
    )
    value["replay_id"] = _expected_replay_id(source_authority=_OWNER_AUTHORITY)
    return value


def test_reason_code_allowlist_is_closed_and_bounded() -> None:
    """Consumers can switch on a published, finite reason vocabulary."""
    assert METADATA_RECEIPT_REASON_CODES == frozenset(
        {
            "admitted_evidence",
            "admitted_owner_disposition",
            "owner_disposition_forbidden",
            "tenant_scope_mismatch",
            "source_authority_mismatch",
            "replay_identity_mismatch",
            "supersession_authority_mismatch",
            "supersession_self_reference",
            "provenance_scope_mismatch",
        }
    )


@pytest.mark.parametrize("status", ["observed", "inferred", "proposed"])
def test_evidence_statuses_are_admitted_with_exact_truth_status(status: str) -> None:
    """A foreign source may report evidence; the receipt never promotes it."""
    value = _envelope_mapping()
    value["truth_status"] = status

    receipt = admit_metadata_observation(value)

    assert receipt.result is MetadataAdmissionResult.ADMITTED
    assert receipt.reason_code == "admitted_evidence"
    assert receipt.observation.truth_status.value == status
    assert receipt.to_mapping()["truth_status"] == status


@pytest.mark.parametrize("status", ["authoritative", "superseded", "rejected"])
def test_foreign_owner_controlled_disposition_is_rejected(status: str) -> None:
    """Foreign promotion or terminal-disposition forgery fails closed."""
    value = _envelope_mapping()
    value["truth_status"] = status

    receipt = admit_metadata_observation(value)

    assert receipt.result is MetadataAdmissionResult.REJECTED
    assert receipt.reason_code == "owner_disposition_forbidden"
    assert receipt.to_mapping()["truth_status"] == status


@pytest.mark.parametrize("status", ["authoritative", "superseded", "rejected"])
def test_subject_owner_may_emit_owner_controlled_dispositions(status: str) -> None:
    """The owning authority alone may publish an owner-controlled disposition."""
    receipt = admit_metadata_observation(_owner_mapping(status))

    assert receipt.result is MetadataAdmissionResult.ADMITTED
    assert receipt.reason_code == "admitted_owner_disposition"


@pytest.mark.parametrize(
    ("value", "reason_code"),
    [
        (
            _mutated(("entity", "source_authority"), "urn:cwl:tenant_001:other_bridge"),
            "source_authority_mismatch",
        ),
        (
            _mutated(
                ("observation_id",),
                "urn:cwl:tenant_001:other_bridge:metadata_observation:"
                f"{_OBSERVATION_UUID}",
            ),
            "source_authority_mismatch",
        ),
        (
            _mutated(
                ("subject_ref",),
                f"urn:cwl:tenant_002:lineage_core:data_table:{_SUBJECT_UUID}",
            ),
            "tenant_scope_mismatch",
        ),
        (
            _mutated(
                ("provenance", "evidence_ref"),
                "urn:cwl:tenant_002:metadata_bridge:metadata_evidence:"
                f"{_SUBJECT_UUID}",
            ),
            "provenance_scope_mismatch",
        ),
        (
            _mutated(("replay_id",), _expected_replay_id(source_release="other-1")),
            "replay_identity_mismatch",
        ),
        (
            _mutated(
                ("supersedes_observation_id",),
                _envelope_mapping()["observation_id"],
            ),
            "supersession_self_reference",
        ),
        (
            _mutated(
                ("supersedes_observation_id",),
                "urn:cwl:tenant_001:other_bridge:metadata_observation:"
                "0195d145-64e8-7f4f-8a23-a0cc784cb712",
            ),
            "supersession_authority_mismatch",
        ),
    ],
)
def test_semantic_violations_produce_bounded_rejected_receipts(
    value: dict[str, Any],
    reason_code: str,
) -> None:
    """Semantic failures are attested as rejected receipts, never admitted."""
    receipt = admit_metadata_observation(value)

    assert receipt.result is MetadataAdmissionResult.REJECTED
    assert receipt.reason_code == reason_code
    assert receipt.reason_code in METADATA_RECEIPT_REASON_CODES


def test_changed_payload_cannot_reuse_a_prior_replay_identity() -> None:
    """New bytes under an old replay ID are rejected, never overwrite a fact."""
    value = _mutated(("payload_sha256",), "1" * 64)

    receipt = admit_metadata_observation(value)

    assert receipt.reason_code == "replay_identity_mismatch"


def test_replayed_observation_yields_an_equal_receipt() -> None:
    """Admission is a pure function: identical input gives identical receipts."""
    first = admit_metadata_observation(_envelope_mapping())
    second = admit_metadata_observation(_envelope_mapping())

    assert first == second
    assert first.to_mapping() == second.to_mapping()


def test_supersession_is_admitted_as_a_new_fact() -> None:
    """A same-authority supersession references the prior fact without edits."""
    prior = _envelope_mapping()
    successor = _mutated(
        ("supersedes_observation_id",),
        prior["observation_id"],
    )
    successor["observation_id"] = (
        f"{_FOREIGN_AUTHORITY}:metadata_observation:"
        "0195d145-64e8-7f4f-8a23-a0cc784cb713"
    )
    successor["event_id"] = "0195d145-64e8-7f4f-8a23-a0cc784cb798"

    receipt = admit_metadata_observation(successor)

    assert receipt.result is MetadataAdmissionResult.ADMITTED
    assert receipt.observation.supersedes_observation_id is not None
    assert admit_metadata_observation(prior).to_mapping()["observation_id"] == (
        prior["observation_id"]
    )


def test_receipt_wire_shape_binds_source_payload_and_contract_versions() -> None:
    """The receipt carries every identity a downstream projection must check."""
    value = _envelope_mapping()

    assert admit_metadata_observation(value).to_mapping() == {
        "result": "admitted",
        "reason_code": "admitted_evidence",
        "observation_id": value["observation_id"],
        "event_id": value["event_id"],
        "subject_ref": value["subject_ref"],
        "truth_status": "observed",
        "source_authority": value["source"]["source_authority"],
        "provider_code": "openmetadata",
        "source_release": value["source"]["source_release"],
        "external_entity_type": value["entity"]["external_entity_type"],
        "external_id": value["entity"]["external_id"],
        "replay_id": value["replay_id"],
        "payload_sha256": value["payload_sha256"],
        "normalized_sha256": value["normalized_sha256"],
        "provenance": value["provenance"],
        "contract_version": "1.0.0",
        "schema_id": (
            "https://schemas.contextualwisdomlab.org/context/"
            "metadata-observation-envelope.v1.schema.json"
        ),
        "profile_id": (
            "urn:cwl:context-contracts:external-metadata-observation-semantics:v1"
        ),
        "profile_version": 1,
        "admission_version": 1,
    }


def test_structural_failures_raise_instead_of_minting_a_receipt() -> None:
    """Nothing trustworthy can be attested about structurally invalid input."""
    with pytest.raises(ValueError, match="provenance is required"):
        admit_metadata_observation(_mutated(("provenance",), None))


def test_receipts_cannot_be_minted_outside_admission() -> None:
    """Direct construction, forged tokens, or field edits are refused."""
    receipt = admit_metadata_observation(_envelope_mapping())
    with pytest.raises(ValueError, match="must come from metadata observation"):
        MetadataProjectionReceipt(
            observation=receipt.observation,
            result=receipt.result,
            reason_code=receipt.reason_code,
        )
    with pytest.raises(ValueError, match="must come from metadata observation"):
        MetadataProjectionReceipt(
            observation=receipt.observation,
            result=receipt.result,
            reason_code=receipt.reason_code,
            _admission_token=object(),
        )
    with pytest.raises(dataclasses.FrozenInstanceError):
        receipt.reason_code = "admitted_owner_disposition"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("changes", "error", "pattern"),
    [
        ({"observation": {}}, TypeError, "MetadataObservationEnvelope"),
        ({"result": "admitted"}, TypeError, "MetadataAdmissionResult"),
        ({"reason_code": "trusted_provider"}, ValueError, "allowlisted"),
        ({"reason_code": "owner_disposition_forbidden"}, ValueError, "disagrees"),
        (
            {"result": MetadataAdmissionResult.REJECTED},
            ValueError,
            "disagrees",
        ),
    ],
)
def test_receipt_state_must_match_its_admission_decision(
    changes: dict[str, object],
    error: type[Exception],
    pattern: str,
) -> None:
    """Even the admission token cannot attest a decision the rules did not make."""
    receipt = admit_metadata_observation(_envelope_mapping())
    arguments: dict[str, object] = {
        "observation": receipt.observation,
        "result": receipt.result,
        "reason_code": receipt.reason_code,
        "_admission_token": admission_module._ADMITTED_METADATA_RECEIPT,
    }
    arguments.update(changes)

    with pytest.raises(error, match=pattern):
        MetadataProjectionReceipt(**arguments)  # type: ignore[arg-type]


def test_admission_requires_a_mapping() -> None:
    """Admission accepts JSON-native mappings or a parsed envelope only."""
    with pytest.raises(TypeError, match="mapping"):
        admit_metadata_observation(["not", "a", "mapping"])  # type: ignore[arg-type]


def test_admission_accepts_a_parsed_envelope() -> None:
    """Callers who parsed JSON text first get the same receipt."""
    envelope = MetadataObservationEnvelope.from_mapping(_envelope_mapping())

    assert admit_metadata_observation(envelope) == admit_metadata_observation(
        _envelope_mapping()
    )


def test_admission_fails_closed_when_packaged_profile_identity_drifts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A receipt cannot claim a profile identity the package does not ship."""
    original = admission_module.load_conformance_profile

    def drifted(name: str) -> dict[str, Any]:
        profile = original(name)
        profile["profile_version"] = 2
        return profile

    monkeypatch.setattr(admission_module, "load_conformance_profile", drifted)

    with pytest.raises(RuntimeError, match="profile identity"):
        admit_metadata_observation(_envelope_mapping())
