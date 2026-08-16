"""Canonical asset URI parsing and construction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import RFC_4122, UUID

_SEGMENT_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,62}$")
_URI_PATTERN = re.compile(
    r"^urn:cwl:(?P<tenant>[a-z][a-z0-9_]{1,62}):"
    r"(?P<authority>[a-z][a-z0-9_]{1,62}):"
    r"(?P<object_type>[a-z][a-z0-9_]{1,62}):"
    r"(?P<object_id>[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12})$"
)


def _validate_segment(value: str, field_name: str) -> str:
    """Return a valid lower-snake URI segment or raise ``ValueError``."""

    if not _SEGMENT_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be lower snake case and 2-63 chars")
    return value


def _validate_uuid7(value: str) -> UUID:
    """Return a parsed RFC 9562 UUIDv7 or raise ``ValueError``."""

    try:
        parsed = UUID(value)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("object_id must be a UUIDv7 string") from exc
    if parsed.version != 7 or parsed.variant != RFC_4122:
        raise ValueError("object_id must use the RFC 9562 UUIDv7 layout")
    return parsed


@dataclass(frozen=True, slots=True)
class CanonicalAssetUri:
    """Stable URI identifying an asset in exactly one authority boundary."""

    tenant_id: str
    authority: str
    object_type: str
    object_id: UUID

    def __post_init__(self) -> None:
        """Validate all URI components after construction."""

        _validate_segment(self.tenant_id, "tenant_id")
        _validate_segment(self.authority, "authority")
        _validate_segment(self.object_type, "object_type")
        _validate_uuid7(str(self.object_id))

    @classmethod
    def parse(cls, value: str) -> CanonicalAssetUri:
        """Parse an exact CWL canonical asset URI."""

        match = _URI_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError("value is not a canonical CWL asset URI")
        groups = match.groupdict()
        return cls(
            tenant_id=groups["tenant"],
            authority=groups["authority"],
            object_type=groups["object_type"],
            object_id=_validate_uuid7(groups["object_id"]),
        )

    @classmethod
    def build(
        cls,
        *,
        tenant_id: str,
        authority: str,
        object_type: str,
        object_id: str | UUID,
    ) -> CanonicalAssetUri:
        """Build a canonical URI from validated components."""

        parsed_id = (
            object_id
            if isinstance(object_id, UUID)
            else _validate_uuid7(object_id)
        )
        return cls(tenant_id, authority, object_type, parsed_id)

    def __str__(self) -> str:
        """Render the canonical URI without normalization side effects."""

        return (
            f"urn:cwl:{self.tenant_id}:{self.authority}:"
            f"{self.object_type}:{self.object_id}"
        )
