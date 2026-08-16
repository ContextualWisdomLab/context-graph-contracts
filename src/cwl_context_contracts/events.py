"""CloudEvents structured-envelope reference implementation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

from .identity import CanonicalAssetUri
from .temporal import _require_aware

_EVENT_TYPE_PATTERN = re.compile(
    r"^org\.contextualwisdomlab\.[a-z0-9_]+(?:\.[a-z0-9_]+)*\.v[1-9][0-9]*$"
)
_EXTENSION_PATTERN = re.compile(r"^[a-z][a-z0-9]{0,19}$")
_RESERVED_NAMES = {
    "specversion",
    "id",
    "source",
    "type",
    "subject",
    "time",
    "datacontenttype",
    "data",
}


@dataclass(frozen=True, slots=True)
class CloudEventEnvelope:
    """Validated CloudEvents 1.0.2 JSON event used between CWL services."""

    event_id: UUID
    source: CanonicalAssetUri
    event_type: str
    subject: CanonicalAssetUri
    event_time: datetime
    data: Mapping[str, Any]
    extensions: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate event type, time, payload, and extension names."""

        if not _EVENT_TYPE_PATTERN.fullmatch(self.event_type):
            raise ValueError("event_type does not follow the CWL reverse-DNS grammar")
        _require_aware(self.event_time, "event_time")
        if not isinstance(self.data, Mapping):
            raise TypeError("data must be a mapping")
        for name, value in self.extensions.items():
            if name in _RESERVED_NAMES or not _EXTENSION_PATTERN.fullmatch(name):
                raise ValueError(f"invalid CloudEvents extension name: {name}")
            if not isinstance(value, str) or not value:
                raise ValueError(f"extension {name} must be a non-empty string")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> CloudEventEnvelope:
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
            event_id = UUID(str(value["id"]))
            event_time = datetime.fromisoformat(
                str(value["time"]).replace("Z", "+00:00")
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("id or time is not parseable") from exc
        extensions = {
            key: item
            for key, item in value.items()
            if key not in _RESERVED_NAMES
        }
        return cls(
            event_id=event_id,
            source=CanonicalAssetUri.parse(str(value["source"])),
            event_type=str(value["type"]),
            subject=CanonicalAssetUri.parse(str(value["subject"])),
            event_time=event_time,
            data=value["data"],
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
        result.update(self.extensions)
        return result
