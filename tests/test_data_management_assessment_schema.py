"""Executable acceptance for framework-neutral assessment-result evidence."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from cwl_context_contracts import (
    available_fixture_names,
    available_schema_names,
    load_fixture,
    load_schema,
)
from tests.conftest import UUID7_TEXT

_SCHEMA_NAME = "data-management-assessment.schema.json"
_FIXTURE_NAME = "data-management-assessment.valid.json"
_ZERO_SHA256 = "0" * 64


def _registry() -> Registry:
    """Return a registry containing every packaged Context Fabric schema."""
    schemas = [load_schema(name) for name in available_schema_names()]
    return Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )


def _validator() -> Draft202012Validator:
    """Return the assessment-result validator with URI formats enabled."""
    return Draft202012Validator(
        load_schema(_SCHEMA_NAME),
        registry=_registry(),
        format_checker=FormatChecker(),
    )


def _valid_result() -> dict[str, Any]:
    """Build original buyer evidence without publisher-owned scoring content."""
    return {
        "contract_version": "1.0.0",
        "assessment_result_id": (
            "urn:cwl:tenant_001:data_context:data_management_assessment:"
            f"{UUID7_TEXT}"
        ),
        "framework_code": "dama_dmbok2r",
        "framework_version": "2024",
        "profile_code": "baseline_data_management",
        "tenant_authority_uri": "urn:cwl:tenant_001:data_context",
        "subject_ref": (
            f"urn:cwl:tenant_001:ea_core:business_capability:{UUID7_TEXT}"
        ),
        "knowledge_cutoff_at": "2026-08-18T00:00:00Z",
        "recorded_at": "2026-08-18T00:00:01Z",
        "overall_score_basis_points": 7600,
        "dimension_scores": [
            {"dimension_code": "engagement", "score_basis_points": 8000},
            {"dimension_code": "evidence", "score_basis_points": 7200},
        ],
        "readiness": "evidence_gap",
        "missing_evidence_codes": ["control_evidence"],
        "truth_status": "observed",
        "provenance": {
            "evidence_ref": (
                "urn:cwl:tenant_001:data_context:assessment_evidence:"
                f"{UUID7_TEXT}"
            ),
            "sha256": _ZERO_SHA256,
            "source_locator": "https://example.com/evidence/assessment-001",
        },
    }


def test_assessment_result_is_packaged_with_a_public_positive_fixture() -> None:
    """Installed consumers can validate the published assessment-result fixture."""
    assert _SCHEMA_NAME in available_schema_names()
    assert _FIXTURE_NAME in available_fixture_names()
    Draft202012Validator.check_schema(load_schema(_SCHEMA_NAME))
    assert list(_validator().iter_errors(load_fixture(_FIXTURE_NAME))) == []


def test_assessment_result_accepts_exact_bounded_scores_and_context() -> None:
    """Assessment evidence carries exact scores, tenant, subject, and cutoff."""
    assert list(_validator().iter_errors(_valid_result())) == []


def test_assessment_result_fails_closed_on_score_and_readiness_inconsistency() -> None:
    """Scores remain exact integers and readiness agrees with evidence gaps."""
    out_of_range = deepcopy(_valid_result())
    out_of_range["overall_score_basis_points"] = 10001
    assert list(_validator().iter_errors(out_of_range))

    non_integer = deepcopy(_valid_result())
    non_integer["dimension_scores"][0]["score_basis_points"] = 75.5
    assert list(_validator().iter_errors(non_integer))

    inconsistent_complete = deepcopy(_valid_result())
    inconsistent_complete["readiness"] = "evidence_complete"
    assert list(_validator().iter_errors(inconsistent_complete))

    missing_gap = deepcopy(_valid_result())
    missing_gap["missing_evidence_codes"] = []
    assert list(_validator().iter_errors(missing_gap))


def test_assessment_result_reuses_canonical_identity_truth_and_time_grammar() -> None:
    """Result evidence cannot weaken shared authority, truth, or timestamp grammar."""
    invalid_values = (
        ("tenant_authority_uri", "https://example.com/tenant"),
        ("subject_ref", "subject-123"),
        ("truth_status", "accepted"),
        ("knowledge_cutoff_at", "2026-08-18"),
    )
    for field_name, invalid_value in invalid_values:
        candidate = deepcopy(_valid_result())
        candidate[field_name] = invalid_value
        assert list(_validator().iter_errors(candidate)), field_name


def test_assessment_result_rejects_embedded_framework_prose() -> None:
    """Public result evidence carries opaque codes, never licensed framework text."""
    candidate = deepcopy(_valid_result())
    candidate["framework_excerpt"] = "Publisher-owned framework prose"
    assert list(_validator().iter_errors(candidate))
