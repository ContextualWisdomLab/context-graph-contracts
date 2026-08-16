"""CloudEvents structured-envelope reference implementation."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from .identity import CanonicalAssetUri, CanonicalAuthorityUri, _validate_uuid7
from .temporal import _require_aware

_EVENT_TYPE_PATTERN = re.compile(
    r"^org\.contextualwisdomlab\.[a-z0-9_]+(?:\.[a-z0-9_]+)*\.v[1-9][0-9]*$"
)
_ABSOLUTE_URI_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:[^\s]+$")
_EXTENSION_PATTERN = re.compile(r"^[a-z][a-z0-9]{0,19}$")
_RESERVED_NAMES = {
    "specversion",
    "id",
    "source",
    "type",
    "subject",
    "time",
    "datacontenttype",
    "dataschema",
    "data",
}


@dataclass(frozen=True, slots=True)
class CloudEventEnvelope:
    """Validated CloudEvents 1.0.2 JSON event used between CWL services."""

    event_id: UUID
    source: CanonicalAuthorityUri
    event_type: str
    subject: CanonicalAssetUri
    event_time: datetime
    data: Mapping[str, Any]
    data_schema: str | None = None
    extensions: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate event identity, type, time, schema, data, and extensions."""
        _validate_uuid7(self.event_id, "event_id")
        if not _EVENT_TYPE_PATTERN.fullmatch(self.event_type):
            raise ValueError("event_type does not follow the CWL reverse-DNS grammar")
        _require_aware(self.event_time, "event_time")
        if not isinstance(self.data, Mapping):
            raise TypeError("data must be a mapping")
        if self.data_schema is not None and not _ABSOLUTE_URI_PATTERN.fullmatch(
            self.data_schema
        ):
            raise ValueError("dataschema must be an absolute URI")
        for name, value in self.extensions.items():
            if name in _RESERVED_NAMES or not _EXTENSION_PATTERN.fullmatch(name):
                raise ValueError(f"invalid CloudEvents extension name: {name}")
            if not isinstance(value, str) or not value:
                raise ValueError(f"extension {name} must be a non-empty string")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CloudEventEnvelope":
        """Parse a CloudEvents structured JSON mapping."""
        if value.get("specversion") != "1.0":
            raise ValueError("specversion must be 1.0")
        if value.get("datacontenttype") != "application/json":
            raise ValueError("datacontenttype must be application/json")
        required = {"id", "source", "type", "subject", "time", "data"}
        missing = required - value.keys()
        if missing:
            raise ValueError(f"missing required attributes: {sorted(missing)!r}")
        try:
            event_id = _validate_uuid7(str(value["id"]), "event_id")
            event_time = datetime.fromisoformat(
                str(value["time"]).replace("Z", "+00:00")
            )
        except (TypeError, ValueError) as exc:
            if "UUIDv7" in str(exc) or "RFC 9562" in str(exc):
                raise
            raise ValueError("id or time is not parseable") from exc
        extensions = {
            key: item for key, item in value.items() if key not in _RESERVED_NAMES
        }
        data_schema = value.get("dataschema")
        return cls(
            event_id=event_id,
            source=CanonicalAuthorityUri.parse(str(value["source"])),
            event_type=str(value["type"]),
            subject=CanonicalAssetUri.parse(str(value["subject"])),
            event_time=event_time,
            data=value["data"],
            data_schema=None if data_schema is None else str(data_schema),
            extensions=extensions,
        )

    def to_mapping(self) -> dict[str, Any]:
        """Serialize the event in CloudEvents structured JSON form."""
        result: dict[str, Any] = {
            "specversion": "1.0",
            "id": str(self.event_id),
            "source": str(self.source),
            "type": self.event_type,
            "subject": str(self.subject),
            "time": self.event_time.isoformat().replace("+00:00", "Z"),
            "datacontenttype": "application/json",
            "data": dict(self.data),
        }
        if self.data_schema is not None:
            result["dataschema"] = self.data_schema
        result.update(self.extensions)
        return result
