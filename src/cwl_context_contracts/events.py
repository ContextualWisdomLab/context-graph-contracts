"""CloudEvents structured-envelope reference implementation."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any
from uuid import UUID

from .identity import CanonicalAssetUri, CanonicalAuthorityUri, _validate_uuid7
from .temporal import (
    _require_aware,
    format_rfc3339_timestamp,
    parse_rfc3339_timestamp,
)

_EVENT_TYPE_PATTERN = re.compile(
    r"^org\.contextualwisdomlab\.[a-z0-9_]+(?:\.[a-z0-9_]+)*\.v[1-9][0-9]*$"
)
_ABSOLUTE_URI_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:[^\s]+$")
_EXTENSION_PATTERN = re.compile(r"^[a-z][a-z0-9]{0,19}$")
_MAX_JSON_DEPTH = 64
_MAX_EXACT_JSON_INTEGER = (2**53) - 1
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


def _require_string(value: Any, field_name: str) -> str:
    """Return a string attribute or raise ``TypeError`` without coercion."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    return value


def _validate_and_freeze_json_value(
    value: Any,
    path: str = "$",
    *,
    depth: int = 0,
    ancestors: frozenset[int] = frozenset(),
) -> Any:
    """Validate one JSON traversal and return a detached immutable snapshot."""
    if depth > _MAX_JSON_DEPTH:
        raise ValueError(f"JSON nesting depth exceeds {_MAX_JSON_DEPTH} at {path}")
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        if abs(value) > _MAX_EXACT_JSON_INTEGER:
            raise ValueError(
                f"JSON integer at {path} exceeds the exact interoperable range "
                f"[-{_MAX_EXACT_JSON_INTEGER}, {_MAX_EXACT_JSON_INTEGER}]"
            )
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"JSON number at {path} must be finite")
        return value
    if isinstance(value, Mapping):
        container_id = id(value)
        if container_id in ancestors:
            raise ValueError(f"JSON container cycle detected at {path}")
        child_ancestors = ancestors | {container_id}
        frozen_items: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"JSON object key at {path} must be a string")
            frozen_items[key] = _validate_and_freeze_json_value(
                item,
                f"{path}.{key}",
                depth=depth + 1,
                ancestors=child_ancestors,
            )
        return MappingProxyType(frozen_items)
    if isinstance(value, list):
        container_id = id(value)
        if container_id in ancestors:
            raise ValueError(f"JSON container cycle detected at {path}")
        child_ancestors = ancestors | {container_id}
        return tuple(
            _validate_and_freeze_json_value(
                item,
                f"{path}[{index}]",
                depth=depth + 1,
                ancestors=child_ancestors,
            )
            for index, item in enumerate(value)
        )
    raise TypeError(f"value at {path} is not JSON-compatible")


def _snapshot_event_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Capture one coherent top-level structured-event traversal."""
    frozen_items: dict[str, Any] = {}
    top_level_ancestors = frozenset({id(value)})
    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError("CloudEvents attribute names must be strings")
        frozen_items[key] = _validate_and_freeze_json_value(
            item,
            f"$.{key}",
            ancestors=top_level_ancestors,
        )
    return MappingProxyType(frozen_items)


def _validate_and_freeze_extensions(value: Mapping[str, str]) -> Mapping[str, str]:
    """Validate extension attributes while snapshotting the same traversal."""
    frozen_items: dict[str, str] = {}
    for name, item in value.items():
        if not isinstance(name, str):
            raise TypeError("CloudEvents extension names must be strings")
        if name in _RESERVED_NAMES or not _EXTENSION_PATTERN.fullmatch(name):
            raise ValueError(f"invalid CloudEvents extension name: {name}")
        if not isinstance(item, str) or not item:
            raise ValueError(f"extension {name} must be a non-empty string")
        frozen_items[name] = item
    return MappingProxyType(frozen_items)


def _thaw_json_value(value: Any) -> Any:
    """Return a fresh JSON-native graph from immutable event state."""
    if isinstance(value, Mapping):
        return {key: _thaw_json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json_value(item) for item in value]
    return value


def _canonical_json_value(value: Any) -> Any:
    """Return an order-stable, type-tagged JSON value for equality and hashing."""
    if isinstance(value, Mapping):
        return (
            "object",
            tuple(
                (key, _canonical_json_value(item))
                for key, item in sorted(value.items())
            ),
        )
    if isinstance(value, tuple):
        return ("array", tuple(_canonical_json_value(item) for item in value))
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("boolean", value)
    if isinstance(value, int):
        return ("integer", value)
    if isinstance(value, float):
        return ("number", value.hex())
    return ("string", value)


@dataclass(frozen=True, slots=True, eq=False)
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
        """Validate and normalize event identity, time, data, and extensions."""
        normalized_event_id = _validate_uuid7(self.event_id, "event_id")
        if type(self.source) is not CanonicalAuthorityUri:
            raise TypeError("source must be a CanonicalAuthorityUri")
        if not isinstance(self.event_type, str):
            raise TypeError("event_type must be a string")
        if not _EVENT_TYPE_PATTERN.fullmatch(self.event_type):
            raise ValueError("event_type does not follow the CWL reverse-DNS grammar")
        if type(self.subject) is not CanonicalAssetUri:
            raise TypeError("subject must be a CanonicalAssetUri")
        if not isinstance(self.event_time, datetime):
            raise TypeError("event_time must be a datetime")
        _require_aware(self.event_time, "event_time")
        if not isinstance(self.data, Mapping):
            raise TypeError("data must be a mapping")
        frozen_data = _validate_and_freeze_json_value(self.data)
        if self.data_schema is not None:
            if not isinstance(self.data_schema, str):
                raise TypeError("data_schema must be a string when present")
            if not _ABSOLUTE_URI_PATTERN.fullmatch(self.data_schema):
                raise ValueError("dataschema must be an absolute URI")
        if self.source.tenant_id != self.subject.tenant_id:
            raise ValueError("source and subject must belong to the same tenant")
        if not isinstance(self.extensions, Mapping):
            raise TypeError("extensions must be a mapping")
        frozen_extensions = _validate_and_freeze_extensions(self.extensions)
        tenant_extension = frozen_extensions.get("tenantid")
        if tenant_extension is not None and tenant_extension != self.source.tenant_id:
            raise ValueError("tenantid extension must match the source tenant")
        object.__setattr__(self, "event_id", normalized_event_id)
        object.__setattr__(self, "data", frozen_data)
        object.__setattr__(self, "extensions", frozen_extensions)

    def _value_key(self) -> tuple[Any, ...]:
        """Return exact semantic event content in a hashable representation."""
        return (
            self.event_id,
            self.source,
            self.event_type,
            self.subject,
            self.event_time,
            _canonical_json_value(self.data),
            self.data_schema,
            tuple(sorted(self.extensions.items())),
        )

    def __eq__(self, other: object) -> bool:
        """Compare full event values with type-exact JSON semantics."""
        return isinstance(other, CloudEventEnvelope) and self._value_key() == (
            other._value_key()
        )

    def __hash__(self) -> int:
        """Hash the same type-exact semantic value used by equality."""
        return hash(self._value_key())

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> CloudEventEnvelope:
        """Parse one coherent snapshot of a CloudEvents structured mapping."""
        if not isinstance(value, Mapping):
            raise TypeError("value must be a mapping")
        snapshot = _snapshot_event_mapping(value)
        required = {
            "specversion",
            "id",
            "source",
            "type",
            "subject",
            "time",
            "datacontenttype",
            "data",
        }
        missing = required - snapshot.keys()
        if missing:
            raise ValueError(f"missing required attributes: {sorted(missing)!r}")
        specversion = _require_string(snapshot["specversion"], "specversion")
        if specversion != "1.0":
            raise ValueError("specversion must be 1.0")
        content_type = _require_string(
            snapshot["datacontenttype"],
            "datacontenttype",
        )
        if content_type != "application/json":
            raise ValueError("datacontenttype must be application/json")
        event_id_text = _require_string(snapshot["id"], "id")
        source_text = _require_string(snapshot["source"], "source")
        event_type = _require_string(snapshot["type"], "type")
        subject_text = _require_string(snapshot["subject"], "subject")
        time_text = _require_string(snapshot["time"], "time")
        event_id = _validate_uuid7(event_id_text, "event_id")
        event_time = parse_rfc3339_timestamp(time_text, "time")
        extensions = {
            key: item
            for key, item in snapshot.items()
            if key not in _RESERVED_NAMES
        }
        raw_data_schema = snapshot.get("dataschema")
        data_schema = (
            None
            if raw_data_schema is None
            else _require_string(raw_data_schema, "dataschema")
        )
        return cls(
            event_id=event_id,
            source=CanonicalAuthorityUri.parse(source_text),
            event_type=event_type,
            subject=CanonicalAssetUri.parse(subject_text),
            event_time=event_time,
            data=_thaw_json_value(snapshot["data"]),
            data_schema=data_schema,
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
            "time": format_rfc3339_timestamp(self.event_time, "time"),
            "datacontenttype": "application/json",
            "data": _thaw_json_value(self.data),
        }
        if self.data_schema is not None:
            result["dataschema"] = self.data_schema
        result.update(self.extensions)
        return result
