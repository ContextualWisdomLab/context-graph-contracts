"""Verify installed conformance evidence against an independently approved manifest."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .conformance_manifest import build_packaged_conformance_manifest

_VERIFICATION_FORMAT = "cwl-context-conformance-verification/v1"
_ACCEPT_ACTION = "accept the installed conformance evidence"
_REPAIR_ACTION = "install the approved contract package or approve this exact manifest"
_INPUT_ACTION = "provide a readable approved conformance manifest JSON object"
_MAX_APPROVED_MANIFEST_BYTES = 1_048_576
_TOP_LEVEL_FIELDS = (
    "manifest_format",
    "distribution_name",
    "distribution_version",
    "algorithm",
)


class ApprovedManifestInputError(ValueError):
    """Raised when an approved-manifest file cannot be safely parsed."""

    def __init__(self, error_code: str) -> None:
        """Store the stable machine-readable manifest input error code."""
        super().__init__(error_code)
        self.error_code = error_code


@dataclass(frozen=True, slots=True)
class ConformanceManifestVerification:
    """Deterministic comparison of approved and installed conformance evidence."""

    installed_distribution_name: str
    installed_distribution_version: str
    mismatches: tuple[str, ...]

    @property
    def verified(self) -> bool:
        """Return whether approved and installed normative evidence match exactly."""
        return not self.mismatches

    @property
    def next_action(self) -> str:
        """Return the buyer action associated with the verification decision."""
        return _ACCEPT_ACTION if self.verified else _REPAIR_ACTION

    def to_mapping(self) -> dict[str, object]:
        """Return stable machine-readable verification evidence."""
        return {
            "verification_format": _VERIFICATION_FORMAT,
            "verified": self.verified,
            "installed_distribution_name": self.installed_distribution_name,
            "installed_distribution_version": self.installed_distribution_version,
            "mismatches": list(self.mismatches),
            "next_action": self.next_action,
        }


def _profile_index(value: object) -> dict[str, str] | None:
    """Return a unique profile-name/digest index or fail closed on malformed shape."""
    if not isinstance(value, list):
        return None
    profile_index: dict[str, str] = {}
    for item in value:
        if not isinstance(item, Mapping):
            return None
        profile_name = item.get("profile_name")
        profile_digest = item.get("sha256")
        if (
            not isinstance(profile_name, str)
            or not isinstance(profile_digest, str)
            or profile_name in profile_index
        ):
            return None
        profile_index[profile_name] = profile_digest
    return profile_index


def verify_packaged_conformance_manifest(
    approved_manifest: object,
) -> ConformanceManifestVerification:
    """Compare an approved manifest with the exact installed semantic resources."""
    installed = build_packaged_conformance_manifest()
    installed_mapping = installed.to_mapping()
    installed_profiles = {
        profile.profile_name: profile.sha256 for profile in installed.profiles
    }
    mismatches: list[str] = []

    if not isinstance(approved_manifest, Mapping):
        mismatches.append("manifest")
    else:
        for field_name in _TOP_LEVEL_FIELDS:
            if approved_manifest.get(field_name) != installed_mapping[field_name]:
                mismatches.append(field_name)

        approved_profiles = _profile_index(approved_manifest.get("profiles"))
        if approved_profiles is None:
            mismatches.append("profiles")
        else:
            approved_profile_count = approved_manifest.get("profile_count")
            if (
                not isinstance(approved_profile_count, int)
                or isinstance(approved_profile_count, bool)
                or approved_profile_count != len(approved_profiles)
            ):
                mismatches.append("profile_count")
            for profile_name, installed_digest in installed_profiles.items():
                approved_digest = approved_profiles.get(profile_name)
                if approved_digest is None:
                    mismatches.append(f"profile_missing:{profile_name}")
                elif approved_digest != installed_digest:
                    mismatches.append(f"profile_sha256:{profile_name}")
            for profile_name in approved_profiles:
                if profile_name not in installed_profiles:
                    mismatches.append(f"profile_unexpected:{profile_name}")

    return ConformanceManifestVerification(
        installed_distribution_name=installed.distribution_name,
        installed_distribution_version=installed.distribution_version,
        mismatches=tuple(mismatches),
    )


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build one JSON object while rejecting ambiguous duplicate member names."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object member: {key}")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(value: str) -> Any:
    """Reject Python JSON extensions such as NaN and Infinity."""
    raise ValueError(f"non-standard JSON constant: {value}")


def load_approved_conformance_manifest(path: Path) -> dict[str, Any]:
    """Read one approved manifest through the shared fail-closed input boundary."""
    try:
        with path.open("rb") as approved_file:
            approved_bytes = approved_file.read(_MAX_APPROVED_MANIFEST_BYTES + 1)
    except OSError as exc:
        raise ApprovedManifestInputError("approved_manifest_unreadable") from exc
    if len(approved_bytes) > _MAX_APPROVED_MANIFEST_BYTES:
        raise ApprovedManifestInputError("approved_manifest_too_large")
    try:
        approved_text = approved_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise ApprovedManifestInputError("approved_manifest_invalid_utf8") from exc
    try:
        approved_payload: Any = json.loads(
            approved_text,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except (ValueError, RecursionError) as exc:
        raise ApprovedManifestInputError("approved_manifest_invalid_json") from exc
    if not isinstance(approved_payload, dict):
        raise ApprovedManifestInputError("approved_manifest_invalid_shape")
    return approved_payload


def _input_failure(error: str) -> int:
    """Print one machine-readable configuration failure and return exit two."""
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
    """Verify an installed package against an approved manifest JSON file."""
    parser = argparse.ArgumentParser(
        description=(
            "Verify installed CWL semantic conformance evidence against an "
            "independently approved manifest."
        )
    )
    parser.add_argument("approved_manifest", type=Path)
    args = parser.parse_args(argv)

    try:
        approved_payload = load_approved_conformance_manifest(args.approved_manifest)
    except ApprovedManifestInputError as exc:
        return _input_failure(exc.error_code)

    report = verify_packaged_conformance_manifest(approved_payload)
    print(json.dumps(report.to_mapping(), sort_keys=True))
    return 0 if report.verified else 1
