"""Compose semantic and complete-bundle evidence into one release-admission gate."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .conformance_admission import (
    ConformanceAdmissionReport,
    evaluate_packaged_conformance_admission,
)
from .conformance_manifest_verifier import (
    ApprovedManifestInputError,
    load_approved_conformance_manifest,
)
from .contract_bundle_manifest_verifier import (
    ContractBundleManifestVerification,
    verify_packaged_contract_bundle_manifest,
)

_ADMISSION_FORMAT = "cwl-context-contract-release-admission/v1"
_READY_ACTION = (
    "obtain qualifying independent approval and verify artifact provenance, "
    "protected-release evidence, and runtime authorization before enabling "
    "the integration"
)
_INPUT_ACTION = (
    "provide readable approved conformance and complete-bundle manifest JSON objects"
)


@dataclass(frozen=True, slots=True)
class ContractReleaseAdmissionReport:
    """Deterministic installed-package evidence used before release admission."""

    conformance_admission: ConformanceAdmissionReport
    bundle_verification: ContractBundleManifestVerification

    @property
    def admitted(self) -> bool:
        """Return whether semantic and complete published-resource evidence pass."""
        return self.conformance_admission.admitted and self.bundle_verification.verified

    @property
    def next_action(self) -> str:
        """Return the smallest buyer action required by the current decision."""
        if not self.conformance_admission.admitted:
            return self.conformance_admission.next_action
        if not self.bundle_verification.verified:
            return self.bundle_verification.next_action
        return _READY_ACTION

    def to_mapping(self) -> dict[str, object]:
        """Return stable machine-readable full release-admission evidence."""
        return {
            "admission_format": _ADMISSION_FORMAT,
            "admitted": self.admitted,
            "installed_distribution_name": (
                self.bundle_verification.installed_distribution_name
            ),
            "installed_distribution_version": (
                self.bundle_verification.installed_distribution_version
            ),
            "conformance_admission": self.conformance_admission.to_mapping(),
            "bundle_verification": self.bundle_verification.to_mapping(),
            "next_action": self.next_action,
        }


def evaluate_packaged_contract_release_admission(
    approved_conformance_manifest: Mapping[str, object],
    approved_bundle_manifest: Mapping[str, object],
) -> ContractReleaseAdmissionReport:
    """Require semantic conformance and exact complete-bundle approved evidence."""
    return ContractReleaseAdmissionReport(
        conformance_admission=evaluate_packaged_conformance_admission(
            approved_conformance_manifest
        ),
        bundle_verification=verify_packaged_contract_bundle_manifest(
            approved_bundle_manifest
        ),
    )


def _input_failure(error: str) -> int:
    """Print one machine-readable approved-input failure and return exit two."""
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
    """Evaluate an installed package against both independently approved manifests."""
    parser = argparse.ArgumentParser(
        description=(
            "Require semantic conformance and exact complete-bundle evidence before "
            "admitting an installed CWL Context Graph contract release."
        )
    )
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

    report = evaluate_packaged_contract_release_admission(
        approved_conformance,
        approved_bundle,
    )
    print(json.dumps(report.to_mapping(), sort_keys=True))
    return 0 if report.admitted else 1
