"""Compose semantic conformance and approved-manifest evidence into one gate."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .conformance_manifest_verifier import (
    ApprovedManifestInputError,
    ConformanceManifestVerification,
    load_approved_conformance_manifest,
    verify_packaged_conformance_manifest,
)
from .conformance_runner import ConformanceReport, run_packaged_conformance

_ADMISSION_FORMAT = "cwl-context-conformance-admission/v1"
_READY_ACTION = (
    "verify artifact provenance and runtime authorization before enabling "
    "the integration"
)
_CONFORMANCE_REPAIR_ACTION = (
    "repair installed semantic conformance before enabling the integration"
)
_INPUT_ACTION = "provide a readable approved conformance manifest JSON object"


@dataclass(frozen=True, slots=True)
class ConformanceAdmissionReport:
    """Combined deterministic evidence used before admitting an installed package."""

    conformance_report: ConformanceReport
    manifest_verification: ConformanceManifestVerification

    @property
    def admitted(self) -> bool:
        """Return whether semantic behavior and approved resource identity both pass."""
        return self.conformance_report.passed and self.manifest_verification.verified

    @property
    def next_action(self) -> str:
        """Return the smallest buyer action required by the current gate result."""
        if not self.conformance_report.passed:
            return _CONFORMANCE_REPAIR_ACTION
        if not self.manifest_verification.verified:
            return self.manifest_verification.next_action
        return _READY_ACTION

    def to_mapping(self) -> dict[str, object]:
        """Return stable machine-readable composite admission evidence."""
        return {
            "admission_format": _ADMISSION_FORMAT,
            "admitted": self.admitted,
            "installed_distribution_name": (
                self.manifest_verification.installed_distribution_name
            ),
            "installed_distribution_version": (
                self.manifest_verification.installed_distribution_version
            ),
            "semantic_conformance": self.conformance_report.to_mapping(),
            "manifest_verification": self.manifest_verification.to_mapping(),
            "next_action": self.next_action,
        }


def evaluate_packaged_conformance_admission(
    approved_manifest: Mapping[str, object],
) -> ConformanceAdmissionReport:
    """Evaluate both installed semantics and exact approved conformance evidence."""
    return ConformanceAdmissionReport(
        conformance_report=run_packaged_conformance(),
        manifest_verification=verify_packaged_conformance_manifest(approved_manifest),
    )


def _input_failure(error: str) -> int:
    """Print one machine-readable admission-input failure and return exit two."""
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
    """Evaluate one installed package against an approved manifest JSON file."""
    parser = argparse.ArgumentParser(
        description=(
            "Require packaged semantic conformance and an exact approved manifest "
            "match before admitting an installed CWL Context Graph contract package."
        )
    )
    parser.add_argument("approved_manifest", type=Path)
    args = parser.parse_args(argv)

    try:
        approved_manifest = load_approved_conformance_manifest(args.approved_manifest)
    except ApprovedManifestInputError as exc:
        return _input_failure(exc.error_code)

    report = evaluate_packaged_conformance_admission(approved_manifest)
    print(json.dumps(report.to_mapping(), sort_keys=True))
    return 0 if report.admitted else 1
