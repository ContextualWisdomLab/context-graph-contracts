"""Provider-neutral external metadata observation interchange contracts.

An external metadata observation records what a foreign catalog reported about
an entity. It is interchange evidence, not catalog state: parsers retain the
supplied truth status exactly and never promote a foreign observation.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from .assertion import _require_mapping
from .conformance_manifest_verifier import (
    _reject_nonstandard_json_constant,
    _unique_json_object,
)
from .events import _is_rfc3986_uri_with_scheme, _validate_and_freeze_json_value
from .identity import (
    CanonicalAssetUri,
    CanonicalAuthorityUri,
    _validate_segment,
    _validate_uuid7,
)
from .provenance import _SHA256_PATTERN, ProvenanceReference
from .temporal import BitemporalInterval
from .truth import TruthStatus, parse_truth_status

METADATA_OBSERVATION_OBJECT_TYPE = "metadata_observation"
_REPLAY_DOMAIN = "cwl-external-metadata-replay/v1"
_MAX_OBSERVATION_JSON_BYTES = 65536
_MAX_SOURCE_RELEASE_LENGTH = 128
_MAX_SCHEMA_URI_LENGTH = 2048
_MAX_EXTERNAL_ID_LENGTH = 512
_MAX_FULLY_QUALIFIED_NAME_LENGTH = 1024
_SOURCE_RELEASE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*")
_SOURCE_FIELDS = frozenset(
    {
        "source_authority",
        "provider_code",
        "source_release",
        "schema_uri",
        "schema_sha256",
        "lifecycle",
    }
)
_ENTITY_FIELDS = frozenset(
    {
        "source_authority",
        "external_entity_type",
        "external_id",
        "fully_qualified_name",
    }
)
_REQUIRED_OBSERVATION_FIELDS = frozenset(
    {
        "observation_id",
        "event_id",
        "source",
        "entity",
        "subject_ref",
        "truth_status",
        "interval",
        "provenance",
        "payload_sha256",
        "normalized_sha256",
        "replay_id",
    }
)
_OBSERVATION_FIELDS = _REQUIRED_OBSERVATION_FIELDS | {"supersedes_observation_id"}


class ExternalMetadataLifecycle(StrEnum):
    """Publication lifecycle of one external metadata source profile."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


def _parse_lifecycle(value: object) -> ExternalMetadataLifecycle:
    """Parse a lifecycle value without case folding or coercion."""
    if type(value) is ExternalMetadataLifecycle:
        return value
    if type(value) is not str:
        raise TypeError("lifecycle must be an ExternalMetadataLifecycle or string")
    try:
        return ExternalMetadataLifecycle(value)
    except ValueError as exc:
        raise ValueError("unknown external metadata lifecycle") from exc


def _require_text(value: object, field_name: str) -> str:
    """Return an exact ``str`` value, rejecting subclasses and other types."""
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a string")
    return value


def _validate_sha256(value: object, field_name: str) -> str:
    """Return one lowercase SHA-256 hexadecimal digest."""
    text = _require_text(value, field_name)
    if not _SHA256_PATTERN.fullmatch(text):
        raise ValueError(f"{field_name} must be 64 lowercase hexadecimal characters")
    return text


def _validate_source_release(value: object) -> str:
    """Return a bounded printable release label without whitespace."""
    text = _require_text(value, "source_release")
    if (
        len(text) > _MAX_SOURCE_RELEASE_LENGTH
        or _SOURCE_RELEASE_PATTERN.fullmatch(text) is None
    ):
        raise ValueError(
            "source_release must contain 1-128 ASCII letters, digits, '.', '_', "
            "'+', or '-' and start with a letter or digit"
        )
    return text


def _validate_opaque_text(value: object, field_name: str, max_length: int) -> str:
    """Return opaque text that is safe to hash and is never normalized."""
    text = _require_text(value, field_name)
    if (
        not 1 <= len(text) <= max_length
        or any(
            unicodedata.category(character) == "Cc"
            or 0xD800 <= ord(character) <= 0xDFFF
            for character in text
        )
    ):
        raise ValueError(
            f"{field_name} must contain 1-{max_length} characters without "
            "control characters or unpaired surrogates"
        )
    return text


def _validate_schema_uri(value: object) -> str:
    """Return an absolute HTTPS schema URI with a host."""
    text = _require_text(value, "schema_uri")
    if (
        len(text) > _MAX_SCHEMA_URI_LENGTH
        or not text.startswith("https://")
        or not _is_rfc3986_uri_with_scheme(text)
        or not urlsplit(text).hostname
    ):
        raise ValueError(
            "schema_uri must be an absolute https URI of at most 2048 characters"
        )
    return text


def _require_observation_uri(value: object, field_name: str) -> CanonicalAssetUri:
    """Return a canonical asset URI identifying a metadata observation."""
    if type(value) is not CanonicalAssetUri:
        raise TypeError(f"{field_name} must be a CanonicalAssetUri")
    if value.object_type != METADATA_OBSERVATION_OBJECT_TYPE:
        raise ValueError(
            f"{field_name} must use object_type {METADATA_OBSERVATION_OBJECT_TYPE}"
        )
    return value


def _snapshot(
    value: object,
    field_name: str,
    allowed: frozenset[str],
    required: frozenset[str],
    label: str,
) -> dict[str, Any]:
    """Capture one mapping traversal and reject unknown or missing members."""
    snapshot = dict(_require_mapping(value, field_name).items())
    unknown = snapshot.keys() - allowed
    if unknown:
        raise ValueError(f"unknown {label} fields: {sorted(unknown)!r}")
    missing = required - snapshot.keys()
    if missing:
        raise ValueError(f"missing required {label} fields: {sorted(missing)!r}")
    return snapshot


def derive_metadata_replay_id(
    *,
    source_authority: CanonicalAuthorityUri,
    external_entity_type: str,
    external_id: str,
    source_release: str,
    payload_sha256: str,
) -> str:
    """Derive the deterministic replay identity for one external observation.

    The digest is SHA-256 over the UTF-8 JSON array
    ``[domain, source_authority, tenant_id, external_entity_type, external_id,
    source_release, payload_sha256]`` without insignificant whitespace. Every
    element is a string, so the encoding is RFC 8785 canonical. Truth status
    and supersession are deliberately excluded; see ADR 0017.
    """
    if type(source_authority) is not CanonicalAuthorityUri:
        raise TypeError("source_authority must be a CanonicalAuthorityUri")
    material = [
        _REPLAY_DOMAIN,
        str(source_authority),
        source_authority.tenant_id,
        _validate_segment(external_entity_type, "external_entity_type"),
        _validate_opaque_text(external_id, "external_id", _MAX_EXTERNAL_ID_LENGTH),
        _validate_source_release(source_release),
        _validate_sha256(payload_sha256, "payload_sha256"),
    ]
    encoded = json.dumps(material, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ExternalMetadataSource:
    """Tenant-scoped identity and schema pin of one external metadata producer.

    ``provider_code`` is a thin profile value such as ``openmetadata``; it never
    grants the provider authority over subjects owned by other contexts.
    """

    source_authority: CanonicalAuthorityUri
    provider_code: str
    source_release: str
    schema_uri: str
    schema_sha256: str
    lifecycle: ExternalMetadataLifecycle

    def __post_init__(self) -> None:
        """Validate authority, provider profile, release, schema pin, and lifecycle."""
        if type(self.source_authority) is not CanonicalAuthorityUri:
            raise TypeError("source_authority must be a CanonicalAuthorityUri")
        _validate_segment(self.provider_code, "provider_code")
        _validate_source_release(self.source_release)
        _validate_schema_uri(self.schema_uri)
        _validate_sha256(self.schema_sha256, "schema_sha256")
        object.__setattr__(self, "lifecycle", _parse_lifecycle(self.lifecycle))

    def to_mapping(self) -> dict[str, str]:
        """Serialize the source to JSON-native wire fields."""
        return {
            "source_authority": str(self.source_authority),
            "provider_code": self.provider_code,
            "source_release": self.source_release,
            "schema_uri": self.schema_uri,
            "schema_sha256": self.schema_sha256,
            "lifecycle": self.lifecycle.value,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ExternalMetadataSource:
        """Parse one coherent snapshot of an external metadata source mapping."""
        snapshot = _snapshot(
            value,
            "source",
            _SOURCE_FIELDS,
            _SOURCE_FIELDS,
            "external metadata source",
        )
        return cls(
            source_authority=CanonicalAuthorityUri.parse(snapshot["source_authority"]),
            provider_code=snapshot["provider_code"],
            source_release=snapshot["source_release"],
            schema_uri=snapshot["schema_uri"],
            schema_sha256=snapshot["schema_sha256"],
            lifecycle=_parse_lifecycle(snapshot["lifecycle"]),
        )


@dataclass(frozen=True, slots=True)
class ExternalEntityReference:
    """Opaque reference to one entity inside a tenant-scoped external source.

    Identity is ``(source_authority, external_entity_type, external_id)``. The
    authority URI carries the tenant, so equal external IDs in different
    tenants never collide. ``external_id`` is never normalized.
    """

    source_authority: CanonicalAuthorityUri
    external_entity_type: str
    external_id: str
    fully_qualified_name: str

    def __post_init__(self) -> None:
        """Validate authority, entity type, opaque ID, and qualified name."""
        if type(self.source_authority) is not CanonicalAuthorityUri:
            raise TypeError("source_authority must be a CanonicalAuthorityUri")
        _validate_segment(self.external_entity_type, "external_entity_type")
        _validate_opaque_text(self.external_id, "external_id", _MAX_EXTERNAL_ID_LENGTH)
        _validate_opaque_text(
            self.fully_qualified_name,
            "fully_qualified_name",
            _MAX_FULLY_QUALIFIED_NAME_LENGTH,
        )

    def to_mapping(self) -> dict[str, str]:
        """Serialize the reference to JSON-native wire fields."""
        return {
            "source_authority": str(self.source_authority),
            "external_entity_type": self.external_entity_type,
            "external_id": self.external_id,
            "fully_qualified_name": self.fully_qualified_name,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ExternalEntityReference:
        """Parse one coherent snapshot of an external entity reference mapping."""
        snapshot = _snapshot(
            value,
            "entity",
            _ENTITY_FIELDS,
            _ENTITY_FIELDS,
            "external entity reference",
        )
        return cls(
            source_authority=CanonicalAuthorityUri.parse(snapshot["source_authority"]),
            external_entity_type=snapshot["external_entity_type"],
            external_id=snapshot["external_id"],
            fully_qualified_name=snapshot["fully_qualified_name"],
        )


@dataclass(frozen=True, slots=True)
class MetadataObservationEnvelope:
    """One immutable, provenance-bound observation reported by an external source.

    The envelope is a data-transfer object. Authority, tenant, and replay
    consistency are decided by ``admit_metadata_observation``, which issues the
    only receipt a consumer may rely on.
    """

    observation_id: CanonicalAssetUri
    event_id: UUID
    source: ExternalMetadataSource
    entity: ExternalEntityReference
    subject_ref: CanonicalAssetUri
    truth_status: TruthStatus
    interval: BitemporalInterval
    provenance: ProvenanceReference
    payload_sha256: str
    normalized_sha256: str
    replay_id: str
    supersedes_observation_id: CanonicalAssetUri | None = None

    def __post_init__(self) -> None:
        """Validate component types and lexical contracts without ranking truth."""
        _require_observation_uri(self.observation_id, "observation_id")
        object.__setattr__(
            self,
            "event_id",
            _validate_uuid7(self.event_id, "event_id"),
        )
        if type(self.source) is not ExternalMetadataSource:
            raise TypeError("source must be an ExternalMetadataSource")
        if type(self.entity) is not ExternalEntityReference:
            raise TypeError("entity must be an ExternalEntityReference")
        if type(self.subject_ref) is not CanonicalAssetUri:
            raise TypeError("subject_ref must be a CanonicalAssetUri")
        object.__setattr__(
            self,
            "truth_status",
            parse_truth_status(self.truth_status),
        )
        if type(self.interval) is not BitemporalInterval:
            raise TypeError("interval must be a BitemporalInterval")
        if type(self.provenance) is not ProvenanceReference:
            raise TypeError("provenance must be a ProvenanceReference")
        _validate_sha256(self.payload_sha256, "payload_sha256")
        _validate_sha256(self.normalized_sha256, "normalized_sha256")
        _validate_sha256(self.replay_id, "replay_id")
        if self.supersedes_observation_id is not None:
            _require_observation_uri(
                self.supersedes_observation_id,
                "supersedes_observation_id",
            )

    def to_mapping(self) -> dict[str, Any]:
        """Serialize the observation to the published JSON object shape."""
        return {
            "observation_id": str(self.observation_id),
            "event_id": str(self.event_id),
            "source": self.source.to_mapping(),
            "entity": self.entity.to_mapping(),
            "subject_ref": str(self.subject_ref),
            "truth_status": self.truth_status.value,
            "interval": self.interval.to_mapping(),
            "provenance": self.provenance.to_mapping(),
            "payload_sha256": self.payload_sha256,
            "normalized_sha256": self.normalized_sha256,
            "replay_id": self.replay_id,
            "supersedes_observation_id": (
                None
                if self.supersedes_observation_id is None
                else str(self.supersedes_observation_id)
            ),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> MetadataObservationEnvelope:
        """Parse one coherent snapshot of a metadata observation mapping."""
        snapshot = _snapshot(
            value,
            "value",
            _OBSERVATION_FIELDS,
            _REQUIRED_OBSERVATION_FIELDS,
            "metadata observation",
        )
        raw_event_id = snapshot["event_id"]
        if type(raw_event_id) is not str:
            raise TypeError("event_id must be a string")
        raw_provenance = snapshot["provenance"]
        if raw_provenance is None:
            raise ValueError("provenance is required for every truth disposition")
        raw_supersedes = snapshot.get("supersedes_observation_id")
        return cls(
            observation_id=CanonicalAssetUri.parse(snapshot["observation_id"]),
            event_id=_validate_uuid7(raw_event_id, "event_id"),
            source=ExternalMetadataSource.from_mapping(snapshot["source"]),
            entity=ExternalEntityReference.from_mapping(snapshot["entity"]),
            subject_ref=CanonicalAssetUri.parse(snapshot["subject_ref"]),
            truth_status=parse_truth_status(snapshot["truth_status"]),
            interval=BitemporalInterval.from_mapping(snapshot["interval"]),
            provenance=ProvenanceReference.from_mapping(raw_provenance),
            payload_sha256=snapshot["payload_sha256"],
            normalized_sha256=snapshot["normalized_sha256"],
            replay_id=snapshot["replay_id"],
            supersedes_observation_id=(
                None
                if raw_supersedes is None
                else CanonicalAssetUri.parse(raw_supersedes)
            ),
        )


def parse_metadata_observation_json(text: str) -> MetadataObservationEnvelope:
    """Parse one strict JSON metadata observation document.

    The boundary rejects input over 64 KiB, invalid Unicode, duplicate object
    members, ``NaN``/``Infinity``, integers outside the exact interoperable
    range, nesting deeper than 64 levels, and non-object documents before any
    contract field is interpreted.
    """
    if not isinstance(text, str):
        raise TypeError("metadata observation JSON must be a string")
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(
            "metadata observation JSON must be valid Unicode text"
        ) from exc
    if len(encoded) > _MAX_OBSERVATION_JSON_BYTES:
        raise ValueError(
            f"metadata observation JSON exceeds {_MAX_OBSERVATION_JSON_BYTES} bytes"
        )
    try:
        decoded = json.loads(
            text,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise ValueError("malformed metadata observation JSON") from exc
    except RecursionError as exc:
        raise ValueError("metadata observation JSON nesting is too deep") from exc
    _validate_and_freeze_json_value(decoded)
    try:
        json.dumps(decoded, ensure_ascii=False).encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(
            "metadata observation JSON must contain Unicode scalar values"
        ) from exc
    if not isinstance(decoded, dict):
        raise ValueError("metadata observation JSON must be a JSON object")
    return MetadataObservationEnvelope.from_mapping(decoded)
