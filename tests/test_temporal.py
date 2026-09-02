"""Bitemporal contract tests."""

from datetime import UTC, datetime, timedelta

import pytest

from cwl_context_contracts import (
    BitemporalInterval,
    format_rfc3339_timestamp,
    parse_rfc3339_timestamp,
)


def test_open_interval_queries_real_and_system_time() -> None:
    """Open validity and knowledge intervals answer independently."""

    start = datetime(2026, 1, 1, tzinfo=UTC)
    recorded = start + timedelta(days=1)
    interval = BitemporalInterval(start, recorded)
    assert interval.is_valid_at(start) is True
    assert interval.was_known_at(start) is False
    assert interval.was_known_at(recorded) is True


def test_closed_interval_uses_exclusive_endpoints() -> None:
    """Closed intervals exclude valid_to and superseded_at instants."""

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = start + timedelta(days=3)
    interval = BitemporalInterval(start, start, end, end)
    assert interval.is_valid_at(end - timedelta(seconds=1)) is True
    assert interval.is_valid_at(end) is False
    assert interval.was_known_at(end - timedelta(seconds=1)) is True
    assert interval.was_known_at(end) is False


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {
                "valid_from": datetime(2026, 1, 1),
                "recorded_at": datetime.now(UTC),
            },
            "valid_from",
        ),
        (
            {
                "valid_from": datetime(2026, 1, 2, tzinfo=UTC),
                "valid_to": datetime(2026, 1, 1, tzinfo=UTC),
                "recorded_at": datetime(2026, 1, 1, tzinfo=UTC),
            },
            "valid_to",
        ),
        (
            {
                "valid_from": datetime(2026, 1, 1, tzinfo=UTC),
                "recorded_at": datetime(2026, 1, 2, tzinfo=UTC),
                "superseded_at": datetime(2026, 1, 1, tzinfo=UTC),
            },
            "superseded_at",
        ),
    ],
)
def test_invalid_intervals_fail_closed(kwargs: dict[str, object], message: str) -> None:
    """Naive and reverse intervals are rejected."""

    with pytest.raises(ValueError, match=message):
        BitemporalInterval(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("valid_from", "2026-01-01T00:00:00Z"),
        ("recorded_at", 1),
        ("valid_to", "2027-01-01T00:00:00Z"),
        ("superseded_at", 1),
    ],
)
def test_interval_constructor_rejects_non_datetime_fields(
    field_name: str,
    field_value: object,
) -> None:
    """Constructor timestamps fail at a stable runtime type boundary."""

    kwargs: dict[str, object] = {
        "valid_from": datetime(2026, 1, 1, tzinfo=UTC),
        "recorded_at": datetime(2026, 1, 2, tzinfo=UTC),
    }
    kwargs[field_name] = field_value
    with pytest.raises(TypeError, match=field_name):
        BitemporalInterval(**kwargs)  # type: ignore[arg-type]


def test_query_rejects_naive_instant() -> None:
    """Temporal queries require an explicit timezone."""

    interval = BitemporalInterval(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="instant"):
        interval.is_valid_at(datetime(2026, 1, 1))
    with pytest.raises(ValueError, match="instant"):
        interval.was_known_at(datetime(2026, 1, 1))


@pytest.mark.parametrize("query_name", ["is_valid_at", "was_known_at"])
def test_query_rejects_non_datetime_instant(query_name: str) -> None:
    """Temporal query methods reject non-datetime values deliberately."""

    interval = BitemporalInterval(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 1, tzinfo=UTC),
    )
    query = getattr(interval, query_name)
    with pytest.raises(TypeError, match="instant"):
        query("2026-01-01T00:00:00Z")


def test_interval_mapping_omits_open_ends_and_round_trips_closed_forms() -> None:
    """Canonical open intervals omit end members instead of emitting JSON null."""
    open_interval = BitemporalInterval(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 2, tzinfo=UTC),
    )
    closed_interval = BitemporalInterval(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 2, tzinfo=UTC),
        datetime(2026, 2, 1, tzinfo=UTC),
        datetime(2026, 2, 2, tzinfo=UTC),
    )
    assert open_interval.to_mapping() == {
        "valid_from": "2026-01-01T00:00:00Z",
        "recorded_at": "2026-01-02T00:00:00Z",
    }
    assert BitemporalInterval.from_mapping(open_interval.to_mapping()) == open_interval
    assert BitemporalInterval.from_mapping(closed_interval.to_mapping()) == (
        closed_interval
    )


@pytest.mark.parametrize("field_name", ["valid_to", "superseded_at"])
def test_interval_mapping_rejects_explicit_null_end_members(field_name: str) -> None:
    """Open ends use omission; an explicit JSON null is not the canonical v1 shape."""
    payload: dict[str, object] = {
        "valid_from": "2026-01-01T00:00:00Z",
        "recorded_at": "2026-01-02T00:00:00Z",
        field_name: None,
    }
    with pytest.raises(TypeError, match=field_name):
        BitemporalInterval.from_mapping(payload)


def test_interval_mapping_rejects_hostile_or_incomplete_input() -> None:
    """Interval parsers snapshot once and fail closed."""
    with pytest.raises(TypeError, match="mapping"):
        BitemporalInterval.from_mapping([])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unknown interval fields"):
        BitemporalInterval.from_mapping(
            {
                "valid_from": "2026-01-01T00:00:00Z",
                "recorded_at": "2026-01-02T00:00:00Z",
                "extra": "no",
            }
        )
    with pytest.raises(ValueError, match="requires valid_from"):
        BitemporalInterval.from_mapping({"valid_from": "2026-01-01T00:00:00Z"})
    with pytest.raises(ValueError, match="RFC 3339"):
        BitemporalInterval.from_mapping(
            {
                "valid_from": "2026-01-01 00:00:00+00:00",
                "recorded_at": "2026-01-02T00:00:00Z",
            }
        )
    with pytest.raises(TypeError, match="valid_from"):
        BitemporalInterval.from_mapping(
            {
                "valid_from": datetime(2026, 1, 1, tzinfo=UTC),
                "recorded_at": "2026-01-02T00:00:00Z",
            }
        )


def test_rfc3339_helpers_reject_non_string_and_naive_values() -> None:
    """Public timestamp helpers keep the same fail-closed boundary."""
    with pytest.raises(TypeError, match="timestamp"):
        parse_rfc3339_timestamp(1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        format_rfc3339_timestamp(datetime(2026, 1, 1))
