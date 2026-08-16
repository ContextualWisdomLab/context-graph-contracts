"""Truth vocabulary tests."""

from cwl_context_contracts import TruthStatus


def test_truth_status_has_stable_ordered_values() -> None:
    """The public vocabulary contains only the six approved statuses."""

    assert [item.value for item in TruthStatus] == [
        "authoritative",
        "observed",
        "inferred",
        "proposed",
        "superseded",
        "rejected",
    ]
