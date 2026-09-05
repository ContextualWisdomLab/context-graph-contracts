"""Compose installed contract and package bytes into one release-evidence gate."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .conformance_manifest_verifier import (
    ApprovedManifestInputError,
    load_approved_conformance_manifest,
)
from .contract_release_admission import (
    ContractReleaseAdmissionReport,
    evaluate_packaged_contract_release_admission,
)
from .package_evidence_verifier import (
    PackageEvidenceInputError,
    PackageEvidenceVerification,
    verify_package_evidence_directory,
)

_ADMISSION_FORMAT = "cwl-context-complete-release-evidence-admission/v1"
_DISTRIBUTION_PREFIX = "cwl_context_contracts-"
_READY_ACTION = (
    "verify artifact attestations bind these exact package bytes to the intended "
    "protected main source commit, generate and independently verify the "
    "attested release-source manifest, then satisfy independent review and "
    "release authorization before publication"
)
_INPUT_ACTION = (
    "provide readable package evidence and approved conformance and complete-bundle "
    "manifest inputs"
)


@dataclass(frozen=True, slots=True)
class ReleaseEvidenceAdmissionReport:
    """One fail-closed decision over installed contracts and exact package bytes."""

    contract_release_admission: ContractReleaseAdmissionReport
    package_evidence_verification: PackageEvidenceVerification
    package_distribution_version: str | None
    release_mismatches: tuple[str, ...]

    @property
    def admitted(self) -> bool:
        """Return whether every deterministic release-evidence layer agrees."""
        return (
            self.contract_release_admission.admitted
            and self.package_evidence_verification.verified
            and not self.release_mismatches
        )

    @property
    def next_action(self) -> str:
        """Return the smallest release-operator action for the current decision."""
        if not self.contract_release_admission.admitted:
            return self.contract_release_admission.next_action
        if not self.package_evidence_verification.verified:
            return self.package_evidence_verification.next_action
        if self.release_mismatches:
            installed_version = (
                self.contract_release_admission.bundle_verification
                .installed_distribution_version
            )
            return (
                "rebuild or reacquire package evidence for installed distribution "
                f"version {installed_version} before provenance verification"
            )
        return _READY_ACTION

    def to_mapping(self) -> dict[str, object]:
        """Return stable machine-readable complete release-evidence admission."""
        bundle_verification = self.contract_release_admission.bundle_verification
        return {
            "admission_format": _ADMISSION_FORMAT,
            "admitted": self.admitted,
            "installed_distribution_name": (
                bundle_verification.installed_distribution_name
            ),
            "installed_distribution_version": (
                bundle_verification.installed_distribution_version
            ),
            "package_distribution_version": self.package_distribution_version,
            "contract_release_admission": (
                self.contract_release_admission.to_mapping()
            ),
            "package_evidence_verification": (
                self.package_evidence_verification.to_mapping()
            ),
            "release_mismatches": list(self.release_mismatches),
            "next_action": self.next_action,
        }


def _verified_package_version(
    package_evidence: PackageEvidenceVerification,
) -> str | None:
    """Return wheel version only after package evidence is verified."""
    if not package_evidence.verified:
        return None
    wheel_name = next(
        artifact.name
        for artifact in package_evidence.artifacts
        if artifact.name.endswith(".whl")
    )
    version_and_tags = wheel_name[len(_DISTRIBUTION_PREFIX) : -len(".whl")]
    return version_and_tags.split("-", maxsplit=1)[0]


def evaluate_release_evidence_admission(
    evidence_directory: Path,
    approved_conformance_manifest: Mapping[str, object],
    approved_bundle_manifest: Mapping[str, object],
) -> ReleaseEvidenceAdmissionReport:
    """Require installed semantic, complete-bundle, and package-byte agreement."""
    contract_admission = evaluate_packaged_contract_release_admission(
        approved_conformance_manifest,
        approved_bundle_manifest,
    )
    package_evidence = verify_package_evidence_directory(evidence_directory)
    package_version = _verified_package_version(package_evidence)
    bundle_verification = contract_admission.bundle_verification
    installed_version = bundle_verification.installed_distribution_version
    release_mismatches = (
        ("package_distribution_version",)
        if package_evidence.verified and package_version != installed_version
        else ()
    )
    return ReleaseEvidenceAdmissionReport(
        contract_release_admission=contract_admission,
        package_evidence_verification=package_evidence,
        package_distribution_version=package_version,
        release_mismatches=release_mismatches,
    )


def _input_failure(error: str) -> int:
    """Print one machine-readable input failure and return exit two."""
    print(
        json.dumps(
            {
                "admission_format": _ADMISSION_FORMAT,
                "admitted": False,
                "error": error,
                "next_action": _INPUT_ACTION,
            },
            sort_keys=True,
        )
    )
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    """Evaluate approved installed contracts and one downloaded package bundle."""
    parser = argparse.ArgumentParser(
        description=(
            "Require installed contract admission and exact matching package evidence "
            "before provenance and protected-main release verification."
        )
    )
    parser.add_argument("evidence_directory", type=Path)
    parser.add_argument("approved_conformance_manifest", type=Path)
    parser.add_argument("approved_bundle_manifest", type=Path)
    args = parser.parse_args(argv)

    try:
        approved_conformance = load_approved_conformance_manifest(
            args.approved_conformance_manifest
        )
        approved_bundle = load_approved_conformance_manifest(
            args.approved_bundle_manifest
        )
    except ApprovedManifestInputError as exc:
        return _input_failure(exc.error_code)

    try:
        report = evaluate_release_evidence_admission(
            args.evidence_directory,
            approved_conformance,
            approved_bundle,
        )
    except PackageEvidenceInputError as exc:
        return _input_failure(exc.error_code)

    print(json.dumps(report.to_mapping(), sort_keys=True))
    return 0 if report.admitted else 1
