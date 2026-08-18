"""Authority-ownership regression for data-management assessment supersession."""

from __future__ import annotations

from copy import deepcopy

import pytest

from cwl_context_contracts import (
    load_fixture,
    validate_data_management_assessment_semantics,
)


def test_assessment_supersession_cannot_cross_same_tenant_authority() -> None:
    """One authority cannot supersede another authority's assessment evidence."""
    candidate = deepcopy(load_fixture("data-management-assessment.valid.json"))
    candidate["supersedes_result_ref"] = (
        "urn:cwl:tenant_001:ea_core:data_management_assessment:"
        "0195d145-64e9-7f4f-8a23-a0cc784cb712"
    )

    with pytest.raises(ValueError, match="same owning authority"):
        validate_data_management_assessment_semantics(candidate)
