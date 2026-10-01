"""Truth-status vocabulary shared by context producers and consumers."""

from enum import StrEnum


class TruthStatus(StrEnum):
    """Evidence status without implying authorization or confidence."""

    AUTHORITATIVE = "authoritative"
    OBSERVED = "observed"
    INFERRED = "inferred"
    PROPOSED = "proposed"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


_TRUTH_RANKS = {
    TruthStatus.REJECTED: 0,
    TruthStatus.SUPERSEDED: 1,
    TruthStatus.PROPOSED: 2,
    TruthStatus.INFERRED: 3,
    TruthStatus.OBSERVED: 4,
    TruthStatus.AUTHORITATIVE: 5,
}
_PROVENANCE_REQUIRED = {
    TruthStatus.AUTHORITATIVE: True,
    TruthStatus.OBSERVED: True,
    TruthStatus.INFERRED: False,
    TruthStatus.PROPOSED: False,
    TruthStatus.SUPERSEDED: False,
    TruthStatus.REJECTED: False,
}


def parse_truth_status(value: object) -> TruthStatus:
    """Parse a truth status without mapping unknown values to a trusted status."""
    if type(value) is TruthStatus:
        return value
    if not isinstance(value, str):
        raise TypeError("truth_status must be a TruthStatus or string")
    try:
        return TruthStatus(value)
    except ValueError as exc:
        raise ValueError("unknown truth status") from exc


def truth_status_rank(status: TruthStatus) -> int:
    """Return the stable legacy ordinal, never an authorization or transition rule."""
    parsed = parse_truth_status(status)
    return _TRUTH_RANKS[parsed]


def requires_provenance(status: TruthStatus) -> bool:
    """Return whether the status must carry a typed provenance reference."""
    parsed = parse_truth_status(status)
    return _PROVENANCE_REQUIRED[parsed]


def refuse_truth_promotion(
    source: TruthStatus,
    target: TruthStatus,
) -> TruthStatus:
    """Return ``target`` only when an adapter preserves the supplied status exactly."""
    parsed_source = parse_truth_status(source)
    parsed_target = parse_truth_status(target)
    if parsed_target is not parsed_source:
        raise ValueError(
            "parsers and adapters cannot promote truth status; "
            "adapters must retain truth status exactly"
        )
    return parsed_target
