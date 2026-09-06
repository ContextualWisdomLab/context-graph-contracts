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
        "The reference package is tested on Python "
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


def test_truth_docs_preserve_origin_and_owner_only_dispositions() -> None:
    """Keep all six statuses explicit without turning them into adapter authority."""
    statuses = (
        "authoritative",
        "observed",
        "inferred",
        "proposed",
        "superseded",
        "rejected",
    )
    documents = {
        "README.md": "retain the supplied status exactly",
        "AGENTS.md": "retain the supplied truth status exactly",
        "docs/ARCHITECTURE.md": "owning product",
        "docs/adr/0003-truth-status.md": "preserve the supplied status exactly",
    }

    for path_name, required_phrase in documents.items():
        text = Path(path_name).read_text(encoding="utf-8").lower()
        for status in statuses:
            assert status in text, f"{path_name} must document {status}"
        assert required_phrase in text, f"{path_name} must document {required_phrase}"


def test_threat_model_preserves_contract_only_security_boundary() -> None:
    """Keep security threats explicit without inventing runtime authority."""
    threat_model = Path("docs/THREAT_MODEL.md").read_text(encoding="utf-8")

    assert "contract-only" in threat_model
    assert "does not authorize" in threat_model
    assert "same-tenant" in threat_model
    assert "replay" in threat_model
    assert "credentials" in threat_model


def test_release_operator_docs_cover_shipped_evidence_and_stateless_rollback() -> None:
    """Keep release evidence, rollback, and product-boundary guidance discoverable."""

    required_content = {
        "docs/OPERABILITY.md": (
            "stateless",
            "conformance",
            "package-evidence-",
        ),
        "docs/PRODUCT_CAPABILITY_CROSSWALK.md": (
            "contract-only",
            "context assertion",
            "out of scope",
        ),
        "docs/RELEASE_AND_ROLLBACK.md": (
            "protected main",
            "SHA256SUMS",
            "rollback",
        ),
        "docs/PROVENANCE.md": (
            "SPDX 3.0.1",
            "SLSA",
            "GitHub artifact attestation",
        ),
    }

    for path_name, expected_tokens in required_content.items():
        text = Path(path_name).read_text(encoding="utf-8")
        lower_text = text.lower()
        for token in expected_tokens:
            assert token.lower() in lower_text, f"{path_name} must document {token}"


def test_product_technical_gap_baseline_preserves_context_fabric_release_boundary() -> None:
    """Keep executable product gaps and immutable-release dependencies explicit."""
    baseline = Path("docs/product-technical-gap-baseline.md").read_text(encoding="utf-8")
    lower_baseline = baseline.lower()

    for token in (
        "contract-only shared kernel",
        "protected `main`",
        "context assertion",
        "immutable release",
        "quarantine sandbox runtime",
        "enterprise-architecture-core",
        "predecessor evidence",
    ):
        assert token in lower_baseline, token
