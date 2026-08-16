"""Bitemporal interval primitives."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

_CWL_TIMESTAMP_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt]"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?"
    r"(?:[Zz]|[+-][0-9]{2}:[0-9]{2})$"
)
_INTERVAL_FIELDS = frozenset(
    {"valid_from", "recorded_at", "valid_to", "superseded_at"}
)


def _require_aware(value: datetime, field_name: str) -> datetime:
    """Return a timezone-aware datetime or raise a deliberate contract error."""

    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def parse_cwl_timestamp(value: str, field_name: str = "timestamp") -> datetime:
    """Parse the CWL timestamp profile, a leap-second-free RFC 3339 subset."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if _CWL_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ValueError(
            f"{field_name} must satisfy the CWL timestamp profile (RFC 3339-derived)"
        )
    normalized = f"{value[:10]}T{value[11:]}"
    if normalized[-1] in {"Z", "z"}:
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must satisfy the CWL timestamp profile (RFC 3339-derived)"
        ) from exc
    return _require_aware(parsed, field_name)


def format_cwl_timestamp(
    value: datetime,
    field_name: str = "timestamp",
) -> str:
    """Serialize an aware instant to the canonical CWL timestamp profile."""
    _require_aware(value, field_name)
    return value.isoformat().replace("+00:00", "Z")


# Pre-release compatibility aliases. The contract name is CWL Timestamp Profile v1.
parse_rfc3339_timestamp = parse_cwl_timestamp
format_rfc3339_timestamp = format_cwl_timestamp


@dataclass(frozen=True, slots=True)
class BitemporalInterval:
    """Real-world validity paired with system-recording history."""

    valid_from: datetime
    recorded_at: datetime
    valid_to: datetime | None = None
    superseded_at: datetime | None = None

    def __post_init__(self) -> None:
        """Reject non-datetime, naive, or non-forward temporal intervals."""

        _require_aware(self.valid_from, "valid_from")
        _require_aware(self.recorded_at, "recorded_at")
        if self.valid_to is not None:
            _require_aware(self.valid_to, "valid_to")
            if self.valid_to <= self.valid_from:
                raise ValueError("valid_to must be later than valid_from")
        if self.superseded_at is not None:
            _require_aware(self.superseded_at, "superseded_at")
            if self.superseded_at < self.recorded_at:
                raise ValueError("superseded_at cannot precede recorded_at")

    def is_valid_at(self, instant: datetime) -> bool:
        """Return whether the fact is valid at a real-world instant."""

        _require_aware(instant, "instant")
        return self.valid_from <= instant and (
            self.valid_to is None or instant < self.valid_to
        )

    def was_known_at(self, instant: datetime) -> bool:
        """Return whether the system knew the fact at an instant."""

        _require_aware(instant, "instant")
        return self.recorded_at <= instant and (
            self.superseded_at is None or instant < self.superseded_at
        )

    def to_mapping(self) -> dict[str, str | None]:
        """Serialize both time dimensions to CWL timestamp wire fields."""
        return {
            "valid_from": format_cwl_timestamp(self.valid_from, "valid_from"),
            "recorded_at": format_cwl_timestamp(self.recorded_at, "recorded_at"),
            "valid_to": (
                None
                if self.valid_to is None
                else format_cwl_timestamp(self.valid_to, "valid_to")
            ),
            "superseded_at": (
                None
                if self.superseded_at is None
                else format_cwl_timestamp(self.superseded_at, "superseded_at")
            ),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> BitemporalInterval:
        """Parse one coherent snapshot of a bitemporal interval mapping."""
        if not isinstance(value, Mapping):
            raise TypeError("value must be a mapping")
        snapshot = dict(value.items())
        unknown = snapshot.keys() - _INTERVAL_FIELDS
        if unknown:
            raise ValueError(f"unknown interval fields: {sorted(unknown)!r}")
        if "valid_from" not in snapshot or "recorded_at" not in snapshot:
            raise ValueError("interval requires valid_from and recorded_at")
        raw_valid_to = snapshot.get("valid_to")
        raw_superseded_at = snapshot.get("superseded_at")
        return cls(
            valid_from=parse_cwl_timestamp(snapshot["valid_from"], "valid_from"),
            recorded_at=parse_cwl_timestamp(
                snapshot["recorded_at"],
                "recorded_at",
            ),
            valid_to=(
                None
                if raw_valid_to is None
                else parse_cwl_timestamp(raw_valid_to, "valid_to")
            ),
            superseded_at=(
                None
                if raw_superseded_at is None
                else parse_cwl_timestamp(raw_superseded_at, "superseded_at")
            ),
        )
