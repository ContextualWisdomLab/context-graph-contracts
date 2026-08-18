"""Verify installed contract resources against an independently approved bundle."""

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
from .contract_bundle_manifest import build_packaged_contract_bundle_manifest

_VERIFICATION_FORMAT = "cwl-context-bundle-verification/v1"
_ACCEPT_ACTION = "accept the installed contract bundle evidence"
_REPAIR_ACTION = (
    "install the approved contract package or approve this exact bundle manifest"
)
_INPUT_ACTION = "provide a readable approved contract bundle manifest JSON object"
_TOP_LEVEL_FIELDS = (
    "manifest_format",
    "distribution_name",
    "distribution_version",
    "algorithm",
)


@dataclass(frozen=True, slots=True)
class ContractBundleManifestVerification:
    """Deterministic comparison of approved and installed contract resources."""

    installed_distribution_name: str
    installed_distribution_version: str
    mismatches: tuple[str, ...]

    @property
    def verified(self) -> bool:
        """Return whether approved and installed bundle evidence match exactly."""
        return not self.mismatches

    @property
    def next_action(self) -> str:
        """Return the buyer action associated with this verification decision."""
        return _ACCEPT_ACTION if self.verified else _REPAIR_ACTION

    def to_mapping(self) -> dict[str, object]:
        """Return stable machine-readable bundle verification evidence."""
        return {
            "verification_format": _VERIFICATION_FORMAT,
            "verified": self.verified,
            "installed_distribution_name": self.installed_distribution_name,
            "installed_distribution_version": self.installed_distribution_version,
            "mismatches": list(self.mismatches),
            "next_action": self.next_action,
        }


def _resource_index(value: object) -> dict[str, str] | None:
    """Return a unique path/digest index or fail closed on malformed evidence."""
    if not isinstance(value, list):
        return None
    resource_index: dict[str, str] = {}
    for item in value:
        if not isinstance(item, Mapping):
            return None
        resource_path = item.get("resource_path")
        resource_digest = item.get("sha256")
        if (
            not isinstance(resource_path, str)
            or not isinstance(resource_digest, str)
            or resource_path in resource_index
        ):
            return None
        resource_index[resource_path] = resource_digest
    return resource_index


def verify_packaged_contract_bundle_manifest(
    approved_manifest: object,
) -> ContractBundleManifestVerification:
    """Compare approved evidence with every exact installed contract resource."""
    installed = build_packaged_contract_bundle_manifest()
    installed_mapping = installed.to_mapping()
    installed_resources = {
        resource.resource_path: resource.sha256 for resource in installed.resources
    }
    mismatches: list[str] = []

    if not isinstance(approved_manifest, Mapping):
        mismatches.append("manifest")
    else:
        for field_name in _TOP_LEVEL_FIELDS:
            if approved_manifest.get(field_name) != installed_mapping[field_name]:
                mismatches.append(field_name)

        approved_resources = _resource_index(approved_manifest.get("resources"))
        if approved_resources is None:
            mismatches.append("resources")
        else:
            approved_resource_count = approved_manifest.get("resource_count")
            if (
                not isinstance(approved_resource_count, int)
                or isinstance(approved_resource_count, bool)
                or approved_resource_count != len(approved_resources)
            ):
                mismatches.append("resource_count")
            for resource_path, installed_digest in installed_resources.items():
                approved_digest = approved_resources.get(resource_path)
                if approved_digest is None:
                    mismatches.append(f"resource_missing:{resource_path}")
                elif approved_digest != installed_digest:
                    mismatches.append(f"resource_sha256:{resource_path}")
            for resource_path in approved_resources:
                if resource_path not in installed_resources:
                    mismatches.append(f"resource_unexpected:{resource_path}")

    return ContractBundleManifestVerification(
        installed_distribution_name=installed.distribution_name,
        installed_distribution_version=installed.distribution_version,
        mismatches=tuple(mismatches),
    )


def _input_failure(error: str) -> int:
    """Print one machine-readable input failure and return exit two."""
    print(
        json.dumps(
            {
                "verification_format": _VERIFICATION_FORMAT,
                "verified": False,
                "error": error,
                "next_action": _INPUT_ACTION,
            },
            sort_keys=True,
        )
    )
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    """Verify an installed package against an approved bundle-manifest file."""
    parser = argparse.ArgumentParser(
        description=(
            "Verify installed CWL contract resources against an independently "
            "approved full bundle manifest."
        )
    )
    parser.add_argument("approved_manifest", type=Path)
    args = parser.parse_args(argv)

    try:
        approved_payload = load_approved_conformance_manifest(args.approved_manifest)
    except ApprovedManifestInputError as exc:
        return _input_failure(exc.error_code)

    report = verify_packaged_contract_bundle_manifest(approved_payload)
    print(json.dumps(report.to_mapping(), sort_keys=True))
    return 0 if report.verified else 1
