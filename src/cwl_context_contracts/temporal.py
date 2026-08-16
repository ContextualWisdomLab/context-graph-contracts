"""Bitemporal interval primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


def _require_aware(value: datetime, field_name: str) -> datetime:
    """Return a timezone-aware datetime or raise a deliberate contract error."""

    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


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
