"""Semantic acceptance for tenant-safe data-management assessment evidence."""

from __future__ import annotations

from copy import deepcopy

import pytest

from cwl_context_contracts import (
    load_fixture,
    validate_data_management_assessment_semantics,
)
from tests.conftest import UUID7_TEXT

_FIXTURE_NAME = "data-management-assessment.valid.json"
_OTHER_UUID7_TEXT = "0195d145-64e9-7f4f-8a23-a0cc784cb712"


def _valid_result() -> dict[str, object]:
    """Return an independent mutable copy of the packaged positive result."""
    return deepcopy(load_fixture(_FIXTURE_NAME))


def test_assessment_semantics_accept_same_tenant_ordered_evidence() -> None:
    """A same-tenant result whose cutoff precedes recording is accepted."""
    assert validate_data_management_assessment_semantics(_valid_result()) is None


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "error_pattern"),
    [
        (
            "tenant_authority_uri",
            "urn:cwl:tenant_002:data_context",
            "tenant authority",
        ),
        (
            "subject_ref",
            f"urn:cwl:tenant_002:ea_core:business_capability:{UUID7_TEXT}",
            "subject",
        ),
    ],
)
def test_assessment_semantics_reject_cross_tenant_primary_references(
    field_name: str,
    invalid_value: str,
    error_pattern: str,
) -> None:
    """Primary authority and subject references cannot cross tenant boundaries."""
    candidate = _valid_result()
    candidate[field_name] = invalid_value
    with pytest.raises(ValueError, match=error_pattern):
        validate_data_management_assessment_semantics(candidate)


def test_assessment_semantics_bind_result_identity_to_declared_authority() -> None:
    """Result identity cannot masquerade as a different same-tenant authority."""
    wrong_authority = _valid_result()
    wrong_authority["tenant_authority_uri"] = "urn:cwl:tenant_001:ea_core"
    with pytest.raises(ValueError, match="assessment result authority"):
        validate_data_management_assessment_semantics(wrong_authority)

    wrong_object_type = _valid_result()
    wrong_object_type["assessment_result_id"] = (
        f"urn:cwl:tenant_001:data_context:business_capability:{UUID7_TEXT}"
    )
    with pytest.raises(ValueError, match="data_management_assessment"):
        validate_data_management_assessment_semantics(wrong_object_type)


def test_assessment_semantics_reject_cross_tenant_provenance() -> None:
    """Evidence provenance must belong to the same tenant as the result."""
    candidate = _valid_result()
    provenance = candidate["provenance"]
    assert isinstance(provenance, dict)
    provenance["evidence_ref"] = (
        f"urn:cwl:tenant_002:data_context:assessment_evidence:{UUID7_TEXT}"
    )
    with pytest.raises(ValueError, match="provenance"):
        validate_data_management_assessment_semantics(candidate)


def test_assessment_semantics_reject_foreign_provenance_authority() -> None:
    """Assessment evidence cannot be relabeled from another same-tenant authority."""
    candidate = _valid_result()
    provenance = candidate["provenance"]
    assert isinstance(provenance, dict)
    provenance["evidence_ref"] = (
        f"urn:cwl:tenant_001:ea_core:assessment_evidence:{UUID7_TEXT}"
    )
    with pytest.raises(ValueError, match="provenance.*authority"):
        validate_data_management_assessment_semantics(candidate)


def test_assessment_semantics_reject_duplicate_dimension_codes() -> None:
    """One dimension code cannot carry two contradictory scores."""
    candidate = _valid_result()
    scores = candidate["dimension_scores"]
    assert isinstance(scores, list)
    scores.append({"dimension_code": "evidence", "score_basis_points": 9100})
    with pytest.raises(ValueError, match="dimension_code values must be unique"):
        validate_data_management_assessment_semantics(candidate)


def test_assessment_semantics_reject_future_knowledge_cutoff() -> None:
    """A result cannot be recorded before the evidence knowledge cutoff."""
    candidate = _valid_result()
    candidate["knowledge_cutoff_at"] = "2026-08-18T00:00:02Z"
    with pytest.raises(ValueError, match="knowledge_cutoff_at"):
        validate_data_management_assessment_semantics(candidate)


def test_assessment_semantics_validate_supersession_identity() -> None:
    """Supersession must reference a different result in the same tenant."""
    same_result = _valid_result()
    same_result["supersedes_result_ref"] = same_result["assessment_result_id"]
    with pytest.raises(ValueError, match="different assessment result"):
        validate_data_management_assessment_semantics(same_result)

    foreign_result = _valid_result()
    foreign_result["supersedes_result_ref"] = (
        "urn:cwl:tenant_002:data_context:data_management_assessment:"
        f"{_OTHER_UUID7_TEXT}"
    )
    with pytest.raises(ValueError, match="superseded result"):
        validate_data_management_assessment_semantics(foreign_result)

    wrong_kind = _valid_result()
    wrong_kind["supersedes_result_ref"] = (
        f"urn:cwl:tenant_001:data_context:business_capability:{_OTHER_UUID7_TEXT}"
    )
    with pytest.raises(ValueError, match="data_management_assessment"):
        validate_data_management_assessment_semantics(wrong_kind)

    valid_supersession = _valid_result()
    valid_supersession["supersedes_result_ref"] = (
        "urn:cwl:tenant_001:data_context:data_management_assessment:"
        f"{_OTHER_UUID7_TEXT}"
    )
    assert validate_data_management_assessment_semantics(valid_supersession) is None


def test_assessment_semantics_fail_closed_on_missing_semantic_fields() -> None:
    """Direct SDK callers cannot bypass the semantic boundary with partial input."""
    candidate = _valid_result()
    del candidate["subject_ref"]
    with pytest.raises(ValueError, match="missing assessment semantic fields"):
        validate_data_management_assessment_semantics(candidate)


def test_assessment_semantics_require_mapping_dimensions() -> None:
    """Direct SDK callers receive stable type errors for malformed score arrays."""
    with pytest.raises(TypeError, match="value must be a mapping"):
        validate_data_management_assessment_semantics([])  # type: ignore[arg-type]

    candidate = _valid_result()
    candidate["dimension_scores"] = "evidence"
    with pytest.raises(TypeError, match="dimension_scores must be a sequence"):
        validate_data_management_assessment_semantics(candidate)

    candidate = _valid_result()
    candidate["dimension_scores"] = ["evidence"]
    with pytest.raises(TypeError, match="dimension_scores must contain mappings"):
        validate_data_management_assessment_semantics(candidate)
