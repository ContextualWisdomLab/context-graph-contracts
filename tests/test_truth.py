"""Truth vocabulary tests."""

import cwl_context_contracts
import pytest

from cwl_context_contracts import (
    TruthStatus,
    parse_truth_status,
    refuse_truth_promotion,
    requires_provenance,
)


def test_truth_status_has_stable_values_without_rank_semantics() -> None:
    """The public vocabulary contains only the six approved non-ranked statuses."""

    assert [item.value for item in TruthStatus] == [
        "authoritative",
        "observed",
        "inferred",
        "proposed",
        "superseded",
        "rejected",
    ]
    assert not hasattr(cwl_context_contracts, "truth_status_rank")


@pytest.mark.parametrize(
    ("status", "needs_evidence"),
    [
        (TruthStatus.REJECTED, False),
        (TruthStatus.SUPERSEDED, False),
        (TruthStatus.PROPOSED, False),
        (TruthStatus.INFERRED, False),
        (TruthStatus.OBSERVED, True),
        (TruthStatus.AUTHORITATIVE, True),
    ],
)
def test_truth_status_local_provenance_requirement_is_explicit(
    status: TruthStatus,
    needs_evidence: bool,
) -> None:
    """Local construction evidence rules stay explicit without implying a rank."""
    assert requires_provenance(status) is needs_evidence
    assert parse_truth_status(status.value) is status


def test_truth_status_parser_rejects_unknown_or_non_string_values() -> None:
    """Unknown labels are not coerced into a more trusted status."""
    with pytest.raises(TypeError, match="truth_status"):
        parse_truth_status(1)
    with pytest.raises(ValueError, match="unknown truth status"):
        parse_truth_status("trusted")


@pytest.mark.parametrize("status", list(TruthStatus))
def test_adapter_truth_guard_allows_exact_status_retention(status: TruthStatus) -> None:
    """A parser or adapter may carry an assertion only without changing status."""
    assert refuse_truth_promotion(status, status) is status


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (TruthStatus.OBSERVED, TruthStatus.REJECTED),
        (TruthStatus.INFERRED, TruthStatus.PROPOSED),
        (TruthStatus.PROPOSED, TruthStatus.AUTHORITATIVE),
        (TruthStatus.REJECTED, TruthStatus.SUPERSEDED),
    ],
)
def test_adapter_truth_guard_rejects_origin_or_disposition_rewrites(
    source: TruthStatus,
    target: TruthStatus,
) -> None:
    """Only an owning domain may issue a new assertion with a different status."""
    with pytest.raises(ValueError, match="retain truth status"):
        refuse_truth_promotion(source, target)
