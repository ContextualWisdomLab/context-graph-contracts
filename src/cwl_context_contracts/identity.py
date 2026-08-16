"""Canonical authority and asset URI parsing and construction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import RFC_4122, UUID

_SEGMENT_GRAMMAR = r"[a-z][a-z0-9]+(?:_[a-z0-9]+)*"
_SEGMENT_PATTERN = re.compile(rf"^{_SEGMENT_GRAMMAR}$")
_AUTHORITY_URI_PATTERN = re.compile(
    rf"^urn:cwl:(?P<tenant>{_SEGMENT_GRAMMAR}):"
    rf"(?P<authority>{_SEGMENT_GRAMMAR})$"
)
_ASSET_URI_PATTERN = re.compile(
    rf"^urn:cwl:(?P<tenant>{_SEGMENT_GRAMMAR}):"
    rf"(?P<authority>{_SEGMENT_GRAMMAR}):"
    rf"(?P<object_type>{_SEGMENT_GRAMMAR}):"
    r"(?P<object_id>[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12})$"
)


def _validate_segment(value: str, field_name: str) -> str:
    """Return a bounded canonical lower-snake segment or raise ``ValueError``."""
    if not 2 <= len(value) <= 63 or not _SEGMENT_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be lower snake case and 2-63 chars")
    return value


def _validate_uuid7(value: str | UUID, field_name: str) -> UUID:
    """Return a parsed RFC 9562 UUIDv7 or raise ``ValueError``."""
    try:
        parsed = value if isinstance(value, UUID) else UUID(value)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a UUIDv7 string") from exc
    if parsed.version != 7 or parsed.variant != RFC_4122:
        raise ValueError(f"{field_name} must use the RFC 9562 UUIDv7 layout")
    return parsed


@dataclass(frozen=True, slots=True)
class CanonicalAuthorityUri:
    """Stable URI identifying one tenant-scoped producer authority."""

    tenant_id: str
    authority: str

    def __post_init__(self) -> None:
        """Validate authority URI components after construction."""
        _validate_segment(self.tenant_id, "tenant_id")
        _validate_segment(self.authority, "authority")

    @classmethod
    def parse(cls, value: str) -> CanonicalAuthorityUri:
        """Parse an exact CWL producer-authority URI."""
        match = _AUTHORITY_URI_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError("value is not a canonical CWL authority URI")
        groups = match.groupdict()
        return cls(
            tenant_id=groups["tenant"],
            authority=groups["authority"],
        )

    @classmethod
    def build(cls, *, tenant_id: str, authority: str) -> CanonicalAuthorityUri:
        """Build an authority URI from validated components."""
        return cls(tenant_id=tenant_id, authority=authority)

    def __str__(self) -> str:
        """Render the canonical authority URI."""
        return f"urn:cwl:{self.tenant_id}:{self.authority}"


@dataclass(frozen=True, slots=True)
class CanonicalAssetUri:
    """Stable URI identifying an asset in exactly one authority boundary."""

    tenant_id: str
    authority: str
    object_type: str
    object_id: UUID

    def __post_init__(self) -> None:
        """Validate all asset URI components after construction."""
        _validate_segment(self.tenant_id, "tenant_id")
        _validate_segment(self.authority, "authority")
        _validate_segment(self.object_type, "object_type")
        _validate_uuid7(self.object_id, "object_id")

    @property
    def authority_uri(self) -> CanonicalAuthorityUri:
        """Return the producer authority that owns this asset identity."""
        return CanonicalAuthorityUri(self.tenant_id, self.authority)

    @classmethod
    def parse(cls, value: str) -> CanonicalAssetUri:
        """Parse an exact CWL canonical asset URI."""
        match = _ASSET_URI_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError("value is not a canonical CWL asset URI")
        groups = match.groupdict()
        return cls(
            tenant_id=groups["tenant"],
            authority=groups["authority"],
            object_type=groups["object_type"],
            object_id=_validate_uuid7(groups["object_id"], "object_id"),
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
        """Build a canonical asset URI from validated components."""
        return cls(
            tenant_id=tenant_id,
            authority=authority,
            object_type=object_type,
            object_id=_validate_uuid7(object_id, "object_id"),
        )

    def __str__(self) -> str:
        """Render the canonical asset URI without normalization side effects."""
        return (
            f"urn:cwl:{self.tenant_id}:{self.authority}:"
            f"{self.object_type}:{self.object_id}"
        )
