"""Truth-status vocabulary shared by context producers and consumers."""

from enum import StrEnum


class TruthStatus(StrEnum):
    """Evidence status without implying authorization, confidence, or rank."""

    AUTHORITATIVE = "authoritative"
    OBSERVED = "observed"
    INFERRED = "inferred"
    PROPOSED = "proposed"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


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


def requires_provenance(status: TruthStatus) -> bool:
    """Return whether local construction requires provenance for this status."""
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
        raise ValueError("parsers and adapters must retain truth status")
    return parsed_target
