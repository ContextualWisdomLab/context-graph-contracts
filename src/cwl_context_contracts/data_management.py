"""Cross-field semantics for framework-neutral data-management assessment evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .identity import CanonicalAssetUri, CanonicalAuthorityUri, _validate_segment
from .provenance import ProvenanceReference
from .temporal import parse_cwl_timestamp

_ASSESSMENT_SEMANTIC_FIELDS = frozenset(
    {
        "assessment_result_id",
        "tenant_authority_uri",
        "subject_ref",
        "knowledge_cutoff_at",
        "recorded_at",
        "dimension_scores",
        "provenance",
    }
)


def validate_data_management_assessment_semantics(
    value: Mapping[str, Any],
) -> None:
    """Fail closed when one assessment result violates cross-field semantics.

    JSON Schema remains the structural contract. This helper enforces invariants
    that Draft 2020-12 cannot express portably: every primary/evidence reference
    belongs to the result tenant, the knowledge cutoff cannot follow recording,
    dimension identifiers are unique, and an optional supersession reference
    identifies a different result in that same tenant.
    """
    if not isinstance(value, Mapping):
        raise TypeError("value must be a mapping")
    snapshot = dict(value.items())
    missing = _ASSESSMENT_SEMANTIC_FIELDS - snapshot.keys()
    if missing:
        raise ValueError(
            f"missing assessment semantic fields: {sorted(missing)!r}"
        )

    assessment_result = CanonicalAssetUri.parse(snapshot["assessment_result_id"])
    tenant_authority = CanonicalAuthorityUri.parse(snapshot["tenant_authority_uri"])
    subject = CanonicalAssetUri.parse(snapshot["subject_ref"])
    provenance = ProvenanceReference.from_mapping(snapshot["provenance"])
    tenant_id = assessment_result.tenant_id

    if tenant_authority.tenant_id != tenant_id:
        raise ValueError("tenant authority must belong to the assessment result tenant")
    if subject.tenant_id != tenant_id:
        raise ValueError("subject must belong to the assessment result tenant")
    if provenance.evidence_ref.tenant_id != tenant_id:
        raise ValueError("provenance must belong to the assessment result tenant")

    knowledge_cutoff = parse_cwl_timestamp(snapshot["knowledge_cutoff_at"])
    recorded_at = parse_cwl_timestamp(snapshot["recorded_at"])
    if knowledge_cutoff > recorded_at:
        raise ValueError("knowledge_cutoff_at cannot be later than recorded_at")

    raw_dimensions = snapshot["dimension_scores"]
    if isinstance(raw_dimensions, (str, bytes)) or not isinstance(
        raw_dimensions,
        Sequence,
    ):
        raise TypeError("dimension_scores must be a sequence")
    seen_dimensions: set[str] = set()
    for item in raw_dimensions:
        if not isinstance(item, Mapping):
            raise TypeError("dimension_scores must contain mappings")
        dimension_code = _validate_segment(item.get("dimension_code"), "dimension_code")
        if dimension_code in seen_dimensions:
            raise ValueError("dimension_code values must be unique")
        seen_dimensions.add(dimension_code)

    raw_supersedes = snapshot.get("supersedes_result_ref")
    if raw_supersedes is None:
        return
    superseded = CanonicalAssetUri.parse(raw_supersedes)
    if superseded == assessment_result:
        raise ValueError("supersedes_result_ref must identify a different assessment result")
    if superseded.tenant_id != tenant_id:
        raise ValueError("superseded result must belong to the assessment result tenant")
