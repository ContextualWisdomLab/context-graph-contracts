"""Truth vocabulary tests."""

import pytest

from cwl_context_contracts import (
    TruthStatus,
    parse_truth_status,
    refuse_truth_promotion,
    requires_provenance,
    truth_status_rank,
)


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


@pytest.mark.parametrize(
    ("status", "rank", "needs_evidence"),
    [
        (TruthStatus.REJECTED, 0, False),
        (TruthStatus.SUPERSEDED, 1, False),
        (TruthStatus.PROPOSED, 2, False),
        (TruthStatus.INFERRED, 3, False),
        (TruthStatus.OBSERVED, 4, True),
        (TruthStatus.AUTHORITATIVE, 5, True),
    ],
)
def test_truth_rank_and_provenance_requirement(
    status: TruthStatus,
    rank: int,
    needs_evidence: bool,
) -> None:
    """Every status has an explicit rank and evidence rule."""
    assert truth_status_rank(status) == rank
    assert requires_provenance(status) is needs_evidence
    assert parse_truth_status(status.value) is status


def test_truth_status_parser_rejects_unknown_or_non_string_values() -> None:
    """Unknown labels are not coerced into a more trusted status."""
    with pytest.raises(TypeError, match="truth_status"):
        parse_truth_status(1)
    with pytest.raises(ValueError, match="unknown truth status"):
        parse_truth_status("trusted")


def test_truth_promotion_is_refused_while_demotion_is_allowed() -> None:
    """Adapters may lower trust or keep it, but they may not raise it."""
    assert (
        refuse_truth_promotion(TruthStatus.OBSERVED, TruthStatus.OBSERVED)
        is TruthStatus.OBSERVED
    )
    assert (
        refuse_truth_promotion(TruthStatus.OBSERVED, TruthStatus.REJECTED)
        is TruthStatus.REJECTED
    )
    with pytest.raises(ValueError, match="cannot promote"):
        refuse_truth_promotion(TruthStatus.INFERRED, TruthStatus.AUTHORITATIVE)
