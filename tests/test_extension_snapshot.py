"""Snapshot-once tests for CloudEvents extension attributes."""

from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from uuid import UUID

from cwl_context_contracts import CloudEventEnvelope
from tests.conftest import EVENT_UUID7_TEXT


class TraversalChangingExtensions(Mapping[str, str]):
    """Expose valid extensions once and hostile values if traversed again."""

    def __init__(self, tenant_id: str) -> None:
        """Store the valid first-pass tenant identifier."""
        self._tenant_id = tenant_id
        self.items_calls = 0

    def __getitem__(self, key: str) -> str:
        """Return the stable tenant value for generic mapping access."""
        if key != "tenantid":
            raise KeyError(key)
        return self._tenant_id

    def __iter__(self) -> Iterator[str]:
        """Iterate the stable extension key."""
        return iter(("tenantid",))

    def __len__(self) -> int:
        """Return the stable extension count."""
        return 1

    def items(self) -> object:
        """Return valid data once and an invalid value on later traversals."""
        self.items_calls += 1
        if self.items_calls == 1:
            return (("tenantid", self._tenant_id),)
        return (("tenantid", object()),)


def test_extensions_are_validated_and_snapshotted_in_one_traversal(
    authority_uri,
    asset_uri,
) -> None:
    """A changing extension mapping cannot swap data after validation."""
    extensions = TraversalChangingExtensions(authority_uri.tenant_id)

    event = CloudEventEnvelope(
        event_id=UUID(EVENT_UUID7_TEXT),
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=datetime(2026, 8, 16, tzinfo=UTC),
        data={},
        extensions=extensions,
    )

    assert event.to_mapping()["tenantid"] == authority_uri.tenant_id
    assert extensions.items_calls == 1
