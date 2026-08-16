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
