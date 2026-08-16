"""Executable consistency checks for customer and contributor documentation."""

import tomllib
from pathlib import Path


def test_contributing_python_matrix_matches_project_metadata() -> None:
    """Keep the documented tested Python versions aligned with classifiers."""
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    versions = [
        value.rsplit(" :: ", 1)[-1]
        for value in project["project"]["classifiers"]
        if value.startswith("Programming Language :: Python :: 3.")
    ]
    expected = (
        "The reference package is tested on "
        + ", ".join(versions[:-1])
        + f", and {versions[-1]}"
    )

    contributing = Path("CONTRIBUTING.md").read_text(encoding="utf-8")
    assert expected in contributing


def test_customer_readme_names_current_semantic_conformance_profiles() -> None:
    """Keep buyer-facing interoperability claims aligned with shipped profiles."""
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "CWL Timestamp Profile v1" in readme
    assert "Context assertion" in readme
    assert "CWL JSON interoperability profile" in readme


def test_threat_model_preserves_contract_only_security_boundary() -> None:
    """Keep security threats explicit without inventing runtime authority."""
    threat_model = Path("docs/THREAT_MODEL.md").read_text(encoding="utf-8")

    assert "contract-only" in threat_model
    assert "does not authorize" in threat_model
    assert "same-tenant" in threat_model
    assert "replay" in threat_model
    assert "credentials" in threat_model
