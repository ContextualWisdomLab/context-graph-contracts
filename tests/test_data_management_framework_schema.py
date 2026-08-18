"""Executable acceptance for framework-neutral data-management contracts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from cwl_context_contracts import available_schema_names, load_schema
from tests.conftest import UUID7_TEXT

_SCHEMA_NAME = "data-management-framework.schema.json"
_ZERO_SHA256 = "0" * 64


def _registry() -> Registry:
    """Return a registry containing every packaged Context Fabric schema."""
    schemas = [load_schema(name) for name in available_schema_names()]
    return Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )


def _validator() -> Draft202012Validator:
    """Return the buyer-facing validator with URI formats enabled."""
    return Draft202012Validator(
        load_schema(_SCHEMA_NAME),
        registry=_registry(),
        format_checker=FormatChecker(),
    )


def _provenance(authority_code: str) -> dict[str, str]:
    """Build realistic same-tenant evidence provenance."""
    return {
        "evidence_ref": (
            f"urn:cwl:tenant_001:{authority_code}:architecture_evidence:{UUID7_TEXT}"
        ),
        "sha256": _ZERO_SHA256,
        "source_locator": "https://dama.org/dama-dmbok-revision/",
    }


def _valid_contract() -> dict[str, Any]:
    """Build an original CWL mapping without redistributing framework content."""
    return {
        "contract_version": "1.0.0",
        "framework_reference": {
            "framework_code": "dama_dmbok2r",
            "framework_version": "2024",
            "publisher_name": "DAMA International",
            "official_reference_uri": "https://dama.org/dama-dmbok-revision/",
            "license_classification": "public_reference",
        },
        "capability_definition": {
            "capability_code": "data_governance_alignment",
            "capability_name": "Data governance alignment",
            "definition_text": (
                "Relate buyer-owned governance outcomes to external framework "
                "references without copying licensed framework content."
            ),
            "source_authority_uri": "urn:cwl:tenant_001:ea_core",
            "truth_status": "proposed",
            "provenance": _provenance("ea_core"),
            "external_framework_ref": "knowledge_area:data_governance",
        },
        "assessment_profile": {
            "profile_code": "baseline_data_management",
            "scoring_dimension_codes": ["engagement", "process", "evidence"],
            "evidence_requirements": [
                {
                    "evidence_code": "governance_policy",
                    "evidence_type": "policy",
                    "authority_uri": "urn:cwl:tenant_001:data_context",
                    "truth_status": "observed",
                    "provenance": _provenance("data_context"),
                }
            ],
        },
    }


def test_framework_contract_is_packaged_and_accepts_public_reference_metadata() -> None:
    """A buyer can validate an original CWL mapping from the installed package."""
    assert _SCHEMA_NAME in available_schema_names()
    Draft202012Validator.check_schema(load_schema(_SCHEMA_NAME))
    assert list(_validator().iter_errors(_valid_contract())) == []


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("framework_reference", "license_classification"), "public_full_text"),
        (("capability_definition", "truth_status"), "accepted"),
        (("capability_definition", "source_authority_uri"), "https://example.com"),
        (
            ("assessment_profile", "evidence_requirements", 0, "truth_status"),
            "accepted",
        ),
    ],
)
def test_framework_contract_reuses_shared_truth_and_authority_grammar(
    path: tuple[str | int, ...],
    value: str,
) -> None:
    """Framework mappings cannot invent weaker truth or authority semantics."""
    candidate = deepcopy(_valid_contract())
    target: Any = candidate
    for segment in path[:-1]:
        target = target[segment]
    target[path[-1]] = value
    assert list(_validator().iter_errors(candidate))


def test_framework_contract_requires_official_reference_and_rejects_copied_body() -> None:
    """Public contracts keep external content as opaque references only."""
    missing_reference = deepcopy(_valid_contract())
    del missing_reference["framework_reference"]["official_reference_uri"]
    assert list(_validator().iter_errors(missing_reference))

    copied_body = deepcopy(_valid_contract())
    copied_body["framework_reference"]["framework_excerpt"] = (
        "Licensed framework prose must not be embedded here."
    )
    assert list(_validator().iter_errors(copied_body))


def test_framework_contract_requires_structured_provenance_for_evidence() -> None:
    """Evidence mappings fail closed on non-canonical provenance identifiers."""
    candidate = deepcopy(_valid_contract())
    requirement = candidate["assessment_profile"]["evidence_requirements"][0]
    requirement["provenance"]["sha256"] = "not-a-digest"
    assert list(_validator().iter_errors(candidate))
