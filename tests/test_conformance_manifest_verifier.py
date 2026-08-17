"""Buyer acceptance for approved conformance-manifest verification."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

import cwl_context_contracts.conformance_manifest_verifier as verifier_module
from cwl_context_contracts import (
    build_packaged_conformance_manifest,
    verify_packaged_conformance_manifest,
)


def _approved_manifest() -> dict[str, object]:
    """Return an independently mutable approved-manifest snapshot."""
    return json.loads(
        json.dumps(build_packaged_conformance_manifest().to_mapping())
    )


def test_exact_approved_manifest_verifies_with_no_mismatches() -> None:
    """An unchanged installed package matches its approved release evidence."""
    report = verify_packaged_conformance_manifest(_approved_manifest())

    assert report.verified is True
    assert report.mismatches == ()
    assert report.to_mapping() == {
        "verification_format": "cwl-context-conformance-verification/v1",
        "verified": True,
        "installed_distribution_name": "cwl-context-contracts",
        "installed_distribution_version": (
            build_packaged_conformance_manifest().distribution_version
        ),
        "mismatches": [],
        "next_action": "accept the installed conformance evidence",
    }


def test_version_drift_fails_closed_with_operator_action() -> None:
    """A different approved package version cannot be treated as equivalent."""
    approved = _approved_manifest()
    approved["distribution_version"] = "999.0.0"

    report = verify_packaged_conformance_manifest(approved)

    assert report.verified is False
    assert report.mismatches == ("distribution_version",)
    assert report.next_action == (
        "install the approved contract package or approve this exact manifest"
    )


def test_profile_digest_drift_identifies_exact_profile() -> None:
    """One changed semantic profile reports its exact evidence identity."""
    approved = _approved_manifest()
    profiles = approved["profiles"]
    assert isinstance(profiles, list)
    first_profile = profiles[0]
    assert isinstance(first_profile, dict)
    profile_name = first_profile["profile_name"]
    first_profile["sha256"] = "0" * 64

    report = verify_packaged_conformance_manifest(approved)

    assert report.verified is False
    assert report.mismatches == (f"profile_sha256:{profile_name}",)


def test_missing_profile_fails_closed() -> None:
    """Approved evidence must cover every installed semantic profile."""
    approved = _approved_manifest()
    profiles = approved["profiles"]
    assert isinstance(profiles, list)
    removed = profiles.pop()
    assert isinstance(removed, dict)
    approved["profile_count"] = len(profiles)

    report = verify_packaged_conformance_manifest(approved)

    assert report.verified is False
    assert report.mismatches == (
        f"profile_missing:{removed['profile_name']}",
    )


def test_unexpected_profile_fails_closed() -> None:
    """An approved manifest cannot silently authorize an unknown profile."""
    approved = _approved_manifest()
    profiles = approved["profiles"]
    assert isinstance(profiles, list)
    profiles.append(
        {
            "profile_name": "unpublished-profile.v1.json",
            "sha256": "1" * 64,
        }
    )
    approved["profile_count"] = len(profiles)

    report = verify_packaged_conformance_manifest(approved)

    assert report.verified is False
    assert report.mismatches == (
        "profile_unexpected:unpublished-profile.v1.json",
    )


def test_profile_count_must_match_approved_profile_list() -> None:
    """The approved manifest cannot lie about the evidence it enumerates."""
    approved = _approved_manifest()
    approved["profile_count"] = 999

    report = verify_packaged_conformance_manifest(approved)

    assert report.verified is False
    assert report.mismatches == ("profile_count",)


def test_non_mapping_manifest_fails_closed() -> None:
    """The public verifier rejects a non-object approved manifest."""
    report = verify_packaged_conformance_manifest([])

    assert report.verified is False
    assert report.mismatches == ("manifest",)


def test_malformed_profiles_shape_fails_closed_without_traceback() -> None:
    """Malformed evidence becomes an actionable verification failure."""
    approved = _approved_manifest()
    approved["profiles"] = "not-a-list"

    report = verify_packaged_conformance_manifest(approved)

    assert report.verified is False
    assert report.mismatches == ("profiles",)


@pytest.mark.parametrize(
    "profiles",
    [
        [None],
        [{"profile_name": 7, "sha256": "0" * 64}],
        [{"profile_name": "x", "sha256": 7}],
        [
            {"profile_name": "x", "sha256": "0" * 64},
            {"profile_name": "x", "sha256": "1" * 64},
        ],
    ],
)
def test_malformed_profile_entries_fail_closed(profiles: list[object]) -> None:
    """Malformed or duplicate profile evidence never becomes authorization."""
    approved = _approved_manifest()
    approved["profiles"] = profiles
    approved["profile_count"] = len(profiles)

    report = verify_packaged_conformance_manifest(approved)

    assert report.verified is False
    assert "profiles" in report.mismatches


def test_verifier_cli_is_installed_by_project_metadata() -> None:
    """Buyers receive the verifier as an installed package command."""
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["scripts"]["cwl-context-conformance-verify"] == (
        "cwl_context_contracts.conformance_manifest_verifier:main"
    )


def test_verifier_cli_accepts_exact_manifest(tmp_path, capsys) -> None:
    """Automation gets deterministic JSON and exit zero for approved bytes."""
    approved_path = tmp_path / "approved.json"
    approved_path.write_text(json.dumps(_approved_manifest()), encoding="utf-8")

    exit_code = verifier_module.main([str(approved_path)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["verified"] is True
    assert payload["mismatches"] == []
    assert captured.err == ""


def test_verifier_cli_rejects_drift_with_nonzero_exit(tmp_path, capsys) -> None:
    """Automation gets exit one when approved and installed evidence diverge."""
    approved = _approved_manifest()
    approved["distribution_version"] = "999.0.0"
    approved_path = tmp_path / "approved.json"
    approved_path.write_text(json.dumps(approved), encoding="utf-8")

    exit_code = verifier_module.main([str(approved_path)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 1
    assert payload["verified"] is False
    assert payload["mismatches"] == ["distribution_version"]
    assert captured.err == ""


def test_verifier_cli_rejects_unreadable_or_invalid_json(tmp_path, capsys) -> None:
    """Configuration failures are machine-readable and fail closed."""
    missing_path = tmp_path / "missing.json"

    missing_exit = verifier_module.main([str(missing_path)])
    missing_payload = json.loads(capsys.readouterr().out)

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{", encoding="utf-8")
    invalid_exit = verifier_module.main([str(invalid_path)])
    invalid_payload = json.loads(capsys.readouterr().out)

    assert missing_exit == 2
    assert missing_payload["verified"] is False
    assert missing_payload["error"] == "approved_manifest_unreadable"
    assert invalid_exit == 2
    assert invalid_payload["verified"] is False
    assert invalid_payload["error"] == "approved_manifest_invalid_json"


def test_verifier_cli_rejects_non_utf8_input_without_traceback(tmp_path, capsys) -> None:
    """Hostile manifest bytes fail closed instead of escaping as Unicode errors."""
    approved_path = tmp_path / "approved.json"
    approved_path.write_bytes(b"\xff\xfe\x00")

    exit_code = verifier_module.main([str(approved_path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["verified"] is False
    assert payload["error"] == "approved_manifest_invalid_utf8"


def test_verifier_cli_rejects_non_object_json(tmp_path, capsys) -> None:
    """A syntactically valid non-object manifest is still invalid evidence."""
    approved_path = tmp_path / "approved.json"
    approved_path.write_text("[]", encoding="utf-8")

    exit_code = verifier_module.main([str(approved_path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["verified"] is False
    assert payload["error"] == "approved_manifest_invalid_shape"
