"""Regression tests for exact truth-status retention at adapter boundaries."""

import pytest

from cwl_context_contracts import TruthStatus
from cwl_context_contracts.truth import refuse_truth_promotion


@pytest.mark.parametrize(
    ("source", "requested"),
    [
        (TruthStatus.AUTHORITATIVE, TruthStatus.OBSERVED),
        (TruthStatus.OBSERVED, TruthStatus.INFERRED),
        (TruthStatus.INFERRED, TruthStatus.PROPOSED),
        (TruthStatus.PROPOSED, TruthStatus.SUPERSEDED),
        (TruthStatus.SUPERSEDED, TruthStatus.REJECTED),
        (TruthStatus.AUTHORITATIVE, TruthStatus.REJECTED),
    ],
)
def test_adapters_cannot_rewrite_truth_disposition(
    source: TruthStatus,
    requested: TruthStatus,
) -> None:
    """A compatibility ordinal must never authorize cross-status rewriting."""

    with pytest.raises(ValueError, match="retain truth status"):
        refuse_truth_promotion(source, requested)


def test_adapters_may_retain_the_exact_supplied_truth_status() -> None:
    """Exact status retention remains a valid adapter operation."""

    for status in TruthStatus:
        assert refuse_truth_promotion(status, status) is status
