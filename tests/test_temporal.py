"""Bitemporal contract tests."""

from datetime import UTC, datetime, timedelta

import pytest

from cwl_context_contracts import BitemporalInterval


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
