"""Build deterministic receipts for packaged conformance admission decisions."""

from __future__ import annotations

import argparse
import hashlib
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

_RECEIPT_FORMAT = "cwl-context-conformance-admission-receipt/v1"
_CANONICALIZATION = "RFC8785"
_DIGEST_ALGORITHM = "sha256"
_INPUT_ACTION = "provide a readable approved conformance manifest JSON object"
_MAX_EXACT_JSON_INTEGER = (2**53) - 1
_MANIFEST_FIELDS = frozenset(
    {
        "manifest_format",
        "distribution_name",
        "distribution_version",
        "algorithm",
        "profile_count",
        "profiles",
    }
)
_STRING_MANIFEST_FIELDS = (
    "manifest_format",
    "distribution_name",
    "distribution_version",
    "algorithm",
)
_PROFILE_FIELDS = frozenset({"profile_name", "sha256"})


def _canonical_json_sha256(value: object) -> str:
    """Return SHA-256 over RFC 8785 JSON for the constrained receipt value set."""
    canonical_json = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def _is_jcs_string(value: object) -> bool:
    """Return whether a value is a Unicode string without unpaired surrogates."""
    return isinstance(value, str) and all(
        not 0xD800 <= ord(character) <= 0xDFFF for character in value
    )


def _validate_manifest_identity_shape(approved_manifest: Mapping[str, object]) -> None:
    """Reject fields or value kinds with no portable receipt-digest semantics."""
    if frozenset(approved_manifest) != _MANIFEST_FIELDS:
        raise ApprovedManifestInputError("approved_manifest_invalid_shape")
    if any(
        not _is_jcs_string(approved_manifest.get(field_name))
        for field_name in _STRING_MANIFEST_FIELDS
    ):
        raise ApprovedManifestInputError("approved_manifest_invalid_shape")

    profile_count = approved_manifest.get("profile_count")
    if (
        not isinstance(profile_count, int)
        or isinstance(profile_count, bool)
        or not 0 <= profile_count <= _MAX_EXACT_JSON_INTEGER
    ):
        raise ApprovedManifestInputError("approved_manifest_invalid_shape")

    profiles = approved_manifest.get("profiles")
    if not isinstance(profiles, list):
        raise ApprovedManifestInputError("approved_manifest_invalid_shape")
    for profile in profiles:
        if not isinstance(profile, Mapping):
            raise ApprovedManifestInputError("approved_manifest_invalid_shape")
        if frozenset(profile) != _PROFILE_FIELDS:
            raise ApprovedManifestInputError("approved_manifest_invalid_shape")
        if not _is_jcs_string(profile.get("profile_name")) or not _is_jcs_string(
            profile.get("sha256")
        ):
            raise ApprovedManifestInputError("approved_manifest_invalid_shape")


@dataclass(frozen=True, slots=True)
class ConformanceAdmissionReceipt:
    """Compact deterministic identity for one conformance admission decision."""

    admission_report: ConformanceAdmissionReport
    approved_manifest_canonical_sha256: str
    admission_evidence_sha256: str

    @property
    def admitted(self) -> bool:
        """Return the admission decision captured by this receipt."""
        return self.admission_report.admitted

    def to_mapping(self) -> dict[str, object]:
        """Return stable machine-readable receipt evidence."""
        verification = self.admission_report.manifest_verification
        return {
            "receipt_format": _RECEIPT_FORMAT,
            "canonicalization": _CANONICALIZATION,
            "digest_algorithm": _DIGEST_ALGORITHM,
            "admitted": self.admitted,
            "installed_distribution_name": verification.installed_distribution_name,
            "installed_distribution_version": verification.installed_distribution_version,
            "approved_manifest_canonical_sha256": (
                self.approved_manifest_canonical_sha256
            ),
            "admission_evidence_sha256": self.admission_evidence_sha256,
            "next_action": self.admission_report.next_action,
        }


def build_packaged_conformance_admission_receipt(
    approved_manifest: Mapping[str, object],
) -> ConformanceAdmissionReceipt:
    """Bind an approved manifest and installed admission result into one receipt."""
    _validate_manifest_identity_shape(approved_manifest)
    admission_report = evaluate_packaged_conformance_admission(approved_manifest)
    return ConformanceAdmissionReceipt(
        admission_report=admission_report,
        approved_manifest_canonical_sha256=_canonical_json_sha256(approved_manifest),
        admission_evidence_sha256=_canonical_json_sha256(admission_report.to_mapping()),
    )


def _input_failure(error: str) -> int:
    """Print one machine-readable receipt-input failure and return exit two."""
    print(
        json.dumps(
            {
                "receipt_format": _RECEIPT_FORMAT,
                "admitted": False,
                "error": error,
                "next_action": _INPUT_ACTION,
            },
            sort_keys=True,
        )
    )
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    """Build one deterministic receipt from an approved manifest JSON file."""
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic receipt for installed CWL Context Graph "
            "conformance admission evidence."
        )
    )
    parser.add_argument("approved_manifest", type=Path)
    args = parser.parse_args(argv)

    try:
        approved_manifest = load_approved_conformance_manifest(args.approved_manifest)
        receipt = build_packaged_conformance_admission_receipt(approved_manifest)
    except ApprovedManifestInputError as exc:
        return _input_failure(exc.error_code)

    print(json.dumps(receipt.to_mapping(), sort_keys=True))
    return 0 if receipt.admitted else 1
