"""Mutation-safety tests for validated CloudEvents envelopes."""

from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest

from cwl_context_contracts import CloudEventEnvelope
from tests.conftest import EVENT_UUID7_TEXT


class TraversalChangingMapping(Mapping[str, Any]):
    """Return a different item graph on the second ``items`` traversal."""

    def __init__(self, second_value: Any) -> None:
        """Store the value that becomes visible after the first traversal."""
        self._second_value = second_value
        self._items_calls = 0

    def __getitem__(self, key: str) -> Any:
        """Expose only the stable first-pass value through key lookup."""
        if key != "safe":
            raise KeyError(key)
        return 1

    def __iter__(self) -> Iterator[str]:
        """Iterate the stable key used by generic Mapping operations."""
        return iter(("safe",))

    def __len__(self) -> int:
        """Return the stable mapping size."""
        return 1

    def items(self) -> Any:
        """Expose safe data once and hostile data on later traversals."""
        self._items_calls += 1
        if self._items_calls == 1:
            return (("safe", 1),)
        return (("unsafe", self._second_value),)


class SecondTraversalCycleMapping(TraversalChangingMapping):
    """Expose a self-cycle only after one safe traversal."""

    def __init__(self) -> None:
        """Initialize without an external second-pass value."""
        super().__init__(None)

    def items(self) -> Any:
        """Return a self-cycle after the safe first traversal."""
        self._items_calls += 1
        if self._items_calls == 1:
            return (("safe", 1),)
        return (("self", self),)


def _event(authority_uri, asset_uri, data: Mapping[str, Any]) -> CloudEventEnvelope:
    """Build one valid event around caller-supplied mapping data."""
    return CloudEventEnvelope(
        event_id=UUID(EVENT_UUID7_TEXT),
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data=data,
        extensions={"tenantid": authority_uri.tenant_id},
    )


def test_event_snapshots_mutable_data_and_extensions(
    authority_uri,
    asset_uri,
) -> None:
    """Caller mutations cannot change an envelope after validation."""
    data = {"nested": {"safe": True}, "items": ["one"]}
    extensions = {"tenantid": authority_uri.tenant_id}
    event = CloudEventEnvelope(
        event_id=UUID(EVENT_UUID7_TEXT),
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data=data,
        extensions=extensions,
    )

    data["nested"]["safe"] = False
    data["items"].append("two")
    extensions["tenantid"] = "tenant_002"

    mapping = event.to_mapping()
    assert mapping["data"] == {"nested": {"safe": True}, "items": ["one"]}
    assert mapping["tenantid"] == authority_uri.tenant_id


def test_event_exposes_only_deeply_immutable_state(
    authority_uri,
    asset_uri,
) -> None:
    """Validated event state cannot be mutated through public containers."""
    event = _event(
        authority_uri,
        asset_uri,
        {"nested": {"safe": True}, "items": ["one"]},
    )

    with pytest.raises(TypeError):
        event.data["new"] = "value"
    with pytest.raises(TypeError):
        event.data["nested"]["safe"] = False
    with pytest.raises(TypeError):
        event.extensions["tenantid"] = "tenant_002"
    with pytest.raises(AttributeError):
        event.data["items"].append("two")

    assert event.to_mapping()["data"] == {
        "nested": {"safe": True},
        "items": ["one"],
    }
    assert event.to_mapping()["tenantid"] == authority_uri.tenant_id


def test_serialized_mapping_cannot_mutate_event_state(
    authority_uri,
    asset_uri,
) -> None:
    """Mutating one serialized copy does not alter later serializations."""
    event = _event(
        authority_uri,
        asset_uri,
        {"nested": {"safe": True}, "items": ["one"]},
    )

    first = event.to_mapping()
    first["data"]["nested"]["safe"] = False
    first["data"]["items"].append("two")
    first["tenantid"] = "tenant_002"

    assert event.to_mapping()["data"] == {
        "nested": {"safe": True},
        "items": ["one"],
    }
    assert event.to_mapping()["tenantid"] == authority_uri.tenant_id


def test_event_freezes_the_same_mapping_traversal_it_validates(
    authority_uri,
    asset_uri,
) -> None:
    """A changing Mapping cannot swap unsafe state after validation."""
    changing = TraversalChangingMapping(object())

    event = _event(authority_uri, asset_uri, changing)

    assert event.to_mapping()["data"] == {"safe": 1}
    assert changing._items_calls == 1


def test_event_never_retraverses_into_a_late_self_cycle(
    authority_uri,
    asset_uri,
) -> None:
    """A second-pass self-cycle is unreachable because input is traversed once."""
    changing = SecondTraversalCycleMapping()

    event = _event(authority_uri, asset_uri, changing)

    assert event.to_mapping()["data"] == {"safe": 1}
    assert changing._items_calls == 1
