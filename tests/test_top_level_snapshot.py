"""Snapshot-once tests for top-level CloudEvents structured mappings."""

from collections.abc import ItemsView, Iterator, KeysView, Mapping
from typing import Any

from cwl_context_contracts import CloudEventEnvelope


class TraversalChangingEvent(Mapping[str, Any]):
    """Expose original values until ``keys`` starts a later logical view."""

    def __init__(self, original: dict[str, Any], changed: dict[str, Any]) -> None:
        """Store the original event and a later incompatible view."""
        self._original = original
        self._changed = changed
        self._changed_view = False
        self.items_calls = 0

    def __getitem__(self, key: str) -> Any:
        """Read from the currently exposed logical view."""
        source = self._changed if self._changed_view else self._original
        return source[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate keys from the currently exposed logical view."""
        source = self._changed if self._changed_view else self._original
        return iter(source)

    def __len__(self) -> int:
        """Return the current logical view size."""
        source = self._changed if self._changed_view else self._original
        return len(source)

    def keys(self) -> KeysView[str]:
        """Switch later key/index reads to the changed logical view."""
        keys = self._original.keys()
        self._changed_view = True
        return keys

    def items(self) -> ItemsView[str, Any]:
        """Expose exactly the current view and count complete traversals."""
        self.items_calls += 1
        source = self._changed if self._changed_view else self._original
        return source.items()


def test_from_mapping_uses_one_coherent_top_level_snapshot(
    authority_uri,
    asset_uri,
) -> None:
    """Parsing never mixes core or payload values from changing mapping views."""
    original = CloudEventEnvelope(
        event_id="0198b84f-d6ce-7b60-8f8c-74eab2d62411",  # type: ignore[arg-type]
        source=authority_uri,
        event_type="org.contextualwisdomlab.ea.lifecycle.changed.v1",
        subject=asset_uri,
        event_time=__import__("datetime").datetime(
            2026,
            8,
            16,
            tzinfo=__import__("datetime").UTC,
        ),
        data={"safe": True},
        extensions={"correlationid": "original"},
    ).to_mapping()
    changed = dict(original)
    changed["data"] = {"safe": False}
    changed["correlationid"] = "changed"
    changing = TraversalChangingEvent(original, changed)

    parsed = CloudEventEnvelope.from_mapping(changing)

    assert parsed.to_mapping()["data"] == {"safe": True}
    assert parsed.to_mapping()["correlationid"] == "original"
    assert changing.items_calls == 1
