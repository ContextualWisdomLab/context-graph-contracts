"""Release-evidence handoff contract for source-bound provenance."""

from __future__ import annotations

from types import SimpleNamespace

from cwl_context_contracts.release_evidence_admission import (
    ReleaseEvidenceAdmissionReport,
)


def test_positive_release_evidence_requires_attested_source_manifest_next() -> None:
    """Package coherence must hand off to source-manifest authentication."""
    contract_admission = SimpleNamespace(
        admitted=True,
        next_action="unused",
        bundle_verification=SimpleNamespace(
            installed_distribution_name="cwl-context-contracts",
            installed_distribution_version="0.1.0",
        ),
    )
    package_evidence = SimpleNamespace(
        verified=True,
        next_action="unused",
    )
    report = ReleaseEvidenceAdmissionReport(
        contract_release_admission=contract_admission,
        package_evidence_verification=package_evidence,
        package_distribution_version="0.1.0",
        release_mismatches=(),
    )

    assert report.admitted is True
    assert report.next_action == (
        "verify artifact attestations bind these exact package bytes to the intended "
        "protected main source commit, generate and independently verify the "
        "attested release-source manifest, then satisfy independent review and "
        "release authorization before publication"
    )
