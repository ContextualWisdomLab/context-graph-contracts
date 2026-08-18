"""Typed context-graph assertions exchanged between independent products."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from .events import CloudEventEnvelope
from .identity import (
    CanonicalAssetUri,
    CanonicalAuthorityUri,
    _validate_segment,
    _validate_uuid7,
)
from .provenance import ProvenanceReference
from .temporal import BitemporalInterval
from .truth import (
    TruthStatus,
    parse_truth_status,
    refuse_truth_promotion,
    requires_provenance,
)

ASSERTION_EVENT_TYPE = "org.contextualwisdomlab.context_graph.assertion.v1"
ASSERTION_DATA_SCHEMA = (
    "https://schemas.contextualwisdomlab.org/context/"
    "context-assertion.v1.schema.json"
)
MAX_MEMBERSHIPS = 16
MAX_MEMBERSHIP_LEVEL = 15
PREDICATE_DERIVED_FROM = "derived_from"
PREDICATE_DEPENDS_ON = "depends_on"
PREDICATE_MEMBER_OF = "member_of"
PREDICATE_DESCRIBES = "describes"
PREDICATE_REALIZED_BY = "realized_by"
PREDICATE_OBSERVED_IN = "observed_in"
_MEMBERSHIP_FIELDS = frozenset(
    {"context_ref", "membership_level", "parent_context_ref"}
)
_ASSERTION_FIELDS = frozenset(
    {
        "assertion_id",
        "subject",
        "predicate",
        "object",
        "truth_status",
        "interval",
        "provenance",
        "memberships",
    }
)


def _require_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    """Return a mapping or raise a stable public type error."""
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    return value


def _require_membership_level(value: object) -> int:
    """Return a bounded integer level, rejecting ``bool`` subclasses."""
    if type(value) is not int:
        raise TypeError("membership_level must be an int")
    if value < 0 or value > MAX_MEMBERSHIP_LEVEL:
        raise ValueError("membership_level must be between 0 and 15")
    return value


@dataclass(frozen=True, slots=True)
class ContextMembership:
    """One affiliation of an assertion with a named context asset.

    Multiple memberships model cross-classified affiliation. A parent context
    records nested structure. Consumers must not treat one membership as the
    only organizational or social unit.
    """

    context_ref: CanonicalAssetUri
    membership_level: int
    parent_context_ref: CanonicalAssetUri | None = None

    def __post_init__(self) -> None:
        """Validate membership identity, level, and optional parent linkage."""
        if type(self.context_ref) is not CanonicalAssetUri:
            raise TypeError("context_ref must be a CanonicalAssetUri")
        object.__setattr__(
            self,
            "membership_level",
            _require_membership_level(self.membership_level),
        )
        if self.parent_context_ref is not None:
            if type(self.parent_context_ref) is not CanonicalAssetUri:
                raise TypeError("parent_context_ref must be a CanonicalAssetUri")
            if self.parent_context_ref == self.context_ref:
                raise ValueError("parent_context_ref must differ from context_ref")
            if self.parent_context_ref.tenant_id != self.context_ref.tenant_id:
                raise ValueError("membership URIs must belong to the same tenant")

    def to_mapping(self) -> dict[str, object]:
        """Serialize one membership to JSON-native fields."""
        return {
            "context_ref": str(self.context_ref),
            "membership_level": self.membership_level,
            "parent_context_ref": (
                None
                if self.parent_context_ref is None
                else str(self.parent_context_ref)
            ),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ContextMembership:
        """Parse one coherent snapshot of a membership mapping."""
        snapshot = dict(_require_mapping(value, "value").items())
        unknown = snapshot.keys() - _MEMBERSHIP_FIELDS
        if unknown:
            raise ValueError(f"unknown membership fields: {sorted(unknown)!r}")
        if "context_ref" not in snapshot or "membership_level" not in snapshot:
            raise ValueError("membership requires context_ref and membership_level")
        raw_parent = snapshot.get("parent_context_ref")
        return cls(
            context_ref=CanonicalAssetUri.parse(snapshot["context_ref"]),
            membership_level=snapshot["membership_level"],
            parent_context_ref=(
                None
                if raw_parent is None
                else CanonicalAssetUri.parse(raw_parent)
            ),
        )


@dataclass(frozen=True, slots=True)
class ContextAssertion:
    """A typed, time-bounded, multi-affiliated statement about two assets.

    The object is an interchange fact, not a graph-store record. Parsers and
    adapters must retain the supplied truth status; they cannot promote
    observed, inferred, or proposed statements to authoritative.
    """

    assertion_id: UUID
    subject: CanonicalAssetUri
    predicate: str
    object: CanonicalAssetUri
    truth_status: TruthStatus
    interval: BitemporalInterval
    memberships: tuple[ContextMembership, ...]
    provenance: ProvenanceReference | None = None

    def __post_init__(self) -> None:
        """Validate identity, affiliation, time, and non-promotion invariants."""
        object.__setattr__(
            self,
            "assertion_id",
            _validate_uuid7(self.assertion_id, "assertion_id"),
        )
        if type(self.subject) is not CanonicalAssetUri:
            raise TypeError("subject must be a CanonicalAssetUri")
        object.__setattr__(
            self,
            "predicate",
            _validate_segment(self.predicate, "predicate"),
        )
        if type(self.object) is not CanonicalAssetUri:
            raise TypeError("object must be a CanonicalAssetUri")
        if self.subject == self.object:
            raise ValueError("subject and object must identify different assets")
        if self.subject.tenant_id != self.object.tenant_id:
            raise ValueError("subject and object must belong to the same tenant")
        object.__setattr__(
            self,
            "truth_status",
            parse_truth_status(self.truth_status),
        )
        if type(self.interval) is not BitemporalInterval:
            raise TypeError("interval must be a BitemporalInterval")
        if isinstance(self.memberships, (str, bytes)) or not isinstance(
            self.memberships,
            Sequence,
        ):
            raise TypeError("memberships must be a sequence")
        frozen_memberships = tuple(self.memberships)
        if not frozen_memberships:
            raise ValueError("memberships must contain at least one context")
        if len(frozen_memberships) > MAX_MEMBERSHIPS:
            raise ValueError("memberships cannot exceed 16 contexts")
        seen_contexts: set[str] = set()
        for membership in frozen_memberships:
            if type(membership) is not ContextMembership:
                raise TypeError("memberships must contain ContextMembership values")
            if membership.context_ref.tenant_id != self.subject.tenant_id:
                raise ValueError("memberships must belong to the subject tenant")
            context_key = str(membership.context_ref)
            if context_key in seen_contexts:
                raise ValueError("membership context_ref values must be unique")
            seen_contexts.add(context_key)
        object.__setattr__(self, "memberships", frozen_memberships)
        if self.provenance is not None:
            if type(self.provenance) is not ProvenanceReference:
                raise TypeError("provenance must be a ProvenanceReference")
            if self.provenance.evidence_ref.tenant_id != self.subject.tenant_id:
                raise ValueError("provenance must belong to the subject tenant")
        elif requires_provenance(self.truth_status):
            raise ValueError("observed and authoritative assertions need provenance")

    def retain_truth_status(self, requested: TruthStatus) -> TruthStatus:
        """Return ``requested`` only when it does not promote this assertion."""
        return refuse_truth_promotion(self.truth_status, requested)

    def to_mapping(self) -> dict[str, Any]:
        """Serialize the assertion to the published JSON object shape."""
        return {
            "assertion_id": str(self.assertion_id),
            "subject": str(self.subject),
            "predicate": self.predicate,
            "object": str(self.object),
            "truth_status": self.truth_status.value,
            "interval": self.interval.to_mapping(),
            "provenance": (
                None if self.provenance is None else self.provenance.to_mapping()
            ),
            "memberships": [
                membership.to_mapping() for membership in self.memberships
            ],
        }

    def into_event(
        self,
        *,
        event_id: UUID,
        source: CanonicalAuthorityUri,
        event_time: datetime,
        extensions: Mapping[str, str] | None = None,
    ) -> CloudEventEnvelope:
        """Wrap the assertion as a provider-neutral CloudEvents payload."""
        return CloudEventEnvelope(
            event_id=event_id,
            source=source,
            event_type=ASSERTION_EVENT_TYPE,
            subject=self.subject,
            event_time=event_time,
            data=self.to_mapping(),
            data_schema=ASSERTION_DATA_SCHEMA,
            extensions={} if extensions is None else extensions,
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ContextAssertion:
        """Parse one coherent snapshot of a context-assertion mapping."""
        snapshot = dict(_require_mapping(value, "value").items())
        unknown = snapshot.keys() - _ASSERTION_FIELDS
        if unknown:
            raise ValueError(f"unknown assertion fields: {sorted(unknown)!r}")
        required = {
            "assertion_id",
            "subject",
            "predicate",
            "object",
            "truth_status",
            "interval",
            "memberships",
        }
        missing = required - snapshot.keys()
        if missing:
            raise ValueError(f"missing required assertion fields: {sorted(missing)!r}")
        raw_assertion_id = snapshot["assertion_id"]
        if not isinstance(raw_assertion_id, str):
            raise TypeError("assertion_id must be a string")
        raw_memberships = snapshot["memberships"]
        if isinstance(raw_memberships, (str, bytes)) or not isinstance(
            raw_memberships,
            Sequence,
        ):
            raise TypeError("memberships must be a sequence")
        raw_provenance = snapshot.get("provenance")
        return cls(
            assertion_id=raw_assertion_id,
            subject=CanonicalAssetUri.parse(snapshot["subject"]),
            predicate=snapshot["predicate"],
            object=CanonicalAssetUri.parse(snapshot["object"]),
            truth_status=parse_truth_status(snapshot["truth_status"]),
            interval=BitemporalInterval.from_mapping(snapshot["interval"]),
            memberships=tuple(
                ContextMembership.from_mapping(item) for item in raw_memberships
            ),
            provenance=(
                None
                if raw_provenance is None
                else ProvenanceReference.from_mapping(raw_provenance)
            ),
        )
