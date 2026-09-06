"""Truth vocabulary tests."""

import pytest

from cwl_context_contracts import (
    TruthStatus,
    parse_truth_status,
    refuse_truth_promotion,
    requires_provenance,
    truth_status_rank,
)


def test_truth_status_has_stable_values() -> None:
    """The public vocabulary contains only the six approved dispositions."""

    assert [item.value for item in TruthStatus] == [
        "authoritative",
        "observed",
        "inferred",
        "proposed",
        "superseded",
        "rejected",
    ]


@pytest.mark.parametrize(
    ("status", "legacy_ordinal"),
    [
        (TruthStatus.REJECTED, 0),
        (TruthStatus.SUPERSEDED, 1),
        (TruthStatus.PROPOSED, 2),
        (TruthStatus.INFERRED, 3),
        (TruthStatus.OBSERVED, 4),
        (TruthStatus.AUTHORITATIVE, 5),
    ],
)
def test_truth_legacy_ordinal_does_not_change_provenance_requirement(
    status: TruthStatus,
    legacy_ordinal: int,
) -> None:
    """Every disposition keeps provenance regardless of its compatibility ordinal."""

    assert truth_status_rank(status) == legacy_ordinal
    assert requires_provenance(status) is True
    assert parse_truth_status(status.value) is status


def test_truth_status_parser_rejects_unknown_or_non_string_values() -> None:
    """Unknown labels are not coerced into a more trusted status."""

    with pytest.raises(TypeError, match="truth_status"):
        parse_truth_status(1)
    with pytest.raises(ValueError, match="unknown truth status"):
        parse_truth_status("trusted")


@pytest.mark.parametrize(
    ("source", "requested"),
    [
        (TruthStatus.AUTHORITATIVE, TruthStatus.OBSERVED),
        (TruthStatus.OBSERVED, TruthStatus.INFERRED),
        (TruthStatus.INFERRED, TruthStatus.PROPOSED),
        (TruthStatus.PROPOSED, TruthStatus.SUPERSEDED),
        (TruthStatus.SUPERSEDED, TruthStatus.REJECTED),
        (TruthStatus.REJECTED, TruthStatus.AUTHORITATIVE),
    ],
)
def test_truth_adapters_cannot_rewrite_disposition(
    source: TruthStatus,
    requested: TruthStatus,
) -> None:
    """Adapters retain producer truth exactly rather than ranking or rewriting it."""

    with pytest.raises(ValueError, match="retain truth status"):
        refuse_truth_promotion(source, requested)


def test_truth_adapters_may_retain_exact_disposition() -> None:
    """Exact producer-supplied truth retention remains valid for every disposition."""

    for status in TruthStatus:
        assert refuse_truth_promotion(status, status) is status
