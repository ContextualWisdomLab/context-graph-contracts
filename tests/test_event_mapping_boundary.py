"""Public structured-event mapping boundary regressions."""

import pytest

from cwl_context_contracts import CloudEventEnvelope


def test_from_mapping_rejects_non_mapping_before_traversal() -> None:
    """Non-mapping public input fails with a deliberate contract type error."""
    with pytest.raises(TypeError, match="value must be a mapping"):
        CloudEventEnvelope.from_mapping([])  # type: ignore[arg-type]
