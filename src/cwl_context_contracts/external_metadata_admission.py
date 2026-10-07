"""Fail-closed admission receipts for external metadata observations.

Admission is a pure function. It never stores replay identities, never ranks
truth status, and never rewrites the observation it attests.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import InitVar, dataclass, field
from enum import StrEnum
from typing import Any

from .assertion import _OWNER_CONTROLLED_TRUTH_STATUSES
from .conformance import load_conformance_profile
from .external_metadata import MetadataObservationEnvelope, derive_metadata_replay_id

METADATA_OBSERVATION_SCHEMA_ID = (
    "https://schemas.contextualwisdomlab.org/context/"
    "metadata-observation-envelope.v1.schema.json"
)
_METADATA_CONTRACT_VERSION = "1.0.0"
_METADATA_PROFILE_NAME = "external-metadata-observation-semantics.v1.json"
_METADATA_PROFILE_ID = (
    "urn:cwl:context-contracts:external-metadata-observation-semantics:v1"
)
_METADATA_PROFILE_VERSION = 1
_METADATA_ADMISSION_VERSION = 1
_ADMITTED_METADATA_RECEIPT = object()
_UNADMITTED_METADATA_RECEIPT = object()

METADATA_RECEIPT_REASON_CODES = frozenset(
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


class MetadataAdmissionResult(StrEnum):
    """Outcome of admitting one external metadata observation."""

    ADMITTED = "admitted"
    REJECTED = "rejected"


def _decide(
    observation: MetadataObservationEnvelope,
) -> tuple[MetadataAdmissionResult, str]:
    """Return the single admission decision the published rules produce."""
    source_authority = observation.source.source_authority
    tenant_id = source_authority.tenant_id
    if (
        observation.entity.source_authority != source_authority
        or observation.observation_id.authority_uri != source_authority
    ):
        return MetadataAdmissionResult.REJECTED, "source_authority_mismatch"
    if observation.subject_ref.tenant_id != tenant_id:
        return MetadataAdmissionResult.REJECTED, "tenant_scope_mismatch"
    if observation.provenance.evidence_ref.tenant_id != tenant_id:
        return MetadataAdmissionResult.REJECTED, "provenance_scope_mismatch"
    expected_replay_id = derive_metadata_replay_id(
        source_authority=source_authority,
        external_entity_type=observation.entity.external_entity_type,
        external_id=observation.entity.external_id,
        source_release=observation.source.source_release,
        payload_sha256=observation.payload_sha256,
    )
    if observation.replay_id != expected_replay_id:
        return MetadataAdmissionResult.REJECTED, "replay_identity_mismatch"
    supersedes = observation.supersedes_observation_id
    if supersedes is not None:
        if supersedes == observation.observation_id:
            return MetadataAdmissionResult.REJECTED, "supersession_self_reference"
        if supersedes.authority_uri != source_authority:
            return (
                MetadataAdmissionResult.REJECTED,
                "supersession_authority_mismatch",
            )
    if observation.truth_status not in _OWNER_CONTROLLED_TRUTH_STATUSES:
        return MetadataAdmissionResult.ADMITTED, "admitted_evidence"
    if observation.subject_ref.authority_uri == source_authority:
        return MetadataAdmissionResult.ADMITTED, "admitted_owner_disposition"
    return MetadataAdmissionResult.REJECTED, "owner_disposition_forbidden"


@dataclass(frozen=True, slots=True)
class MetadataProjectionReceipt:
    """Attestation of one admission decision over one external observation.

    Only ``admit_metadata_observation`` can mint a receipt. The receipt carries
    the exact observation, the bounded reason code, and the contract, profile,
    and admission versions that produced the decision.
    """

    observation: MetadataObservationEnvelope
    result: MetadataAdmissionResult
    reason_code: str
    contract_version: str = field(default=_METADATA_CONTRACT_VERSION, init=False)
    schema_id: str = field(default=METADATA_OBSERVATION_SCHEMA_ID, init=False)
    profile_id: str = field(default=_METADATA_PROFILE_ID, init=False)
    profile_version: int = field(default=_METADATA_PROFILE_VERSION, init=False)
    admission_version: int = field(default=_METADATA_ADMISSION_VERSION, init=False)
    _admission_token: InitVar[object] = _UNADMITTED_METADATA_RECEIPT

    def __post_init__(self, _admission_token: object) -> None:
        """Reject forged receipts or decisions the admission rules did not make."""
        if type(self.observation) is not MetadataObservationEnvelope:
            raise TypeError("observation must be a MetadataObservationEnvelope")
        if type(self.result) is not MetadataAdmissionResult:
            raise TypeError("result must be a MetadataAdmissionResult")
        if self.reason_code not in METADATA_RECEIPT_REASON_CODES:
            raise ValueError("reason_code must be an allowlisted receipt reason")
        if _decide(self.observation) != (self.result, self.reason_code):
            raise ValueError("receipt decision disagrees with admission rules")
        if _admission_token is not _ADMITTED_METADATA_RECEIPT:
            raise ValueError(
                "receipt must come from metadata observation admission"
            )

    def to_mapping(self) -> dict[str, Any]:
        """Serialize the receipt to the published JSON object shape."""
        observation = self.observation
        return {
            "result": self.result.value,
            "reason_code": self.reason_code,
            "observation_id": str(observation.observation_id),
            "event_id": str(observation.event_id),
            "subject_ref": str(observation.subject_ref),
            "truth_status": observation.truth_status.value,
            "source_authority": str(observation.source.source_authority),
            "provider_code": observation.source.provider_code,
            "source_release": observation.source.source_release,
            "external_entity_type": observation.entity.external_entity_type,
            "external_id": observation.entity.external_id,
            "replay_id": observation.replay_id,
            "payload_sha256": observation.payload_sha256,
            "normalized_sha256": observation.normalized_sha256,
            "provenance": observation.provenance.to_mapping(),
            "contract_version": self.contract_version,
            "schema_id": self.schema_id,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "admission_version": self.admission_version,
        }


def _validate_packaged_profile_identity() -> None:
    """Fail closed when the packaged profile identity drifts from the contract."""
    profile = load_conformance_profile(_METADATA_PROFILE_NAME)
    if (
        profile.get("profile_id") != _METADATA_PROFILE_ID
        or profile.get("profile_version") != _METADATA_PROFILE_VERSION
    ):
        raise RuntimeError(
            "packaged external metadata observation profile identity does not "
            "match the receipt contract"
        )


def admit_metadata_observation(
    value: Mapping[str, Any] | MetadataObservationEnvelope,
) -> MetadataProjectionReceipt:
    """Admit or reject one external metadata observation.

    Structural, type, and grammar failures raise ``TypeError`` or
    ``ValueError`` and mint no receipt. Semantic failures return a rejected
    receipt with an allowlisted reason code. A foreign source may report
    ``observed``, ``inferred``, or ``proposed`` evidence; only the subject's
    owning authority may report ``authoritative``, ``superseded``, or
    ``rejected``.
    """
    _validate_packaged_profile_identity()
    if type(value) is MetadataObservationEnvelope:
        observation = value
    elif isinstance(value, Mapping):
        observation = MetadataObservationEnvelope.from_mapping(value)
    else:
        raise TypeError("metadata observation must be a mapping or envelope")
    result, reason_code = _decide(observation)
    return MetadataProjectionReceipt(
        observation=observation,
        result=result,
        reason_code=reason_code,
        _admission_token=_ADMITTED_METADATA_RECEIPT,
    )
