"""Buyer acceptance for approved full contract-bundle verification."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

import cwl_context_contracts.contract_bundle_manifest_verifier as verifier_module
from cwl_context_contracts import (
    build_packaged_contract_bundle_manifest,
    verify_packaged_contract_bundle_manifest,
)


def _approved_manifest() -> dict[str, object]:
    """Return an independently mutable installed-bundle evidence snapshot."""
    return json.loads(
        json.dumps(build_packaged_contract_bundle_manifest().to_mapping())
    )


def test_exact_approved_bundle_verifies_with_no_mismatches() -> None:
    """An unchanged installed package matches all approved resource bytes."""
    report = verify_packaged_contract_bundle_manifest(_approved_manifest())

    assert report.verified is True
    assert report.mismatches == ()
    assert report.to_mapping() == {
        "verification_format": "cwl-context-bundle-verification/v1",
        "verified": True,
        "installed_distribution_name": "cwl-context-contracts",
        "installed_distribution_version": (
            build_packaged_contract_bundle_manifest().distribution_version
        ),
        "mismatches": [],
        "next_action": "accept the installed contract bundle evidence",
    }


@pytest.mark.parametrize(
    "field_name,replacement",
    [
        ("manifest_format", "unapproved-format"),
        ("distribution_name", "unapproved-distribution"),
        ("distribution_version", "999.0.0"),
        ("algorithm", "sha512"),
    ],
)
def test_top_level_bundle_identity_drift_fails_closed(
    field_name: str,
    replacement: str,
) -> None:
    """Approved package identity fields must match the installed bundle."""
    approved = _approved_manifest()
    approved[field_name] = replacement

    report = verify_packaged_contract_bundle_manifest(approved)

    assert report.verified is False
    assert report.mismatches == (field_name,)
    assert report.next_action == (
        "install the approved contract package or approve this exact bundle manifest"
    )


def test_resource_digest_drift_identifies_exact_resource() -> None:
    """One changed resource reports its stable package-relative evidence identity."""
    approved = _approved_manifest()
    resources = approved["resources"]
    assert isinstance(resources, list)
    first_resource = resources[0]
    assert isinstance(first_resource, dict)
    resource_path = first_resource["resource_path"]
    first_resource["sha256"] = "0" * 64

    report = verify_packaged_contract_bundle_manifest(approved)

    assert report.verified is False
    assert report.mismatches == (f"resource_sha256:{resource_path}",)


def test_missing_resource_fails_closed() -> None:
    """Approved evidence must cover every installed published resource."""
    approved = _approved_manifest()
    resources = approved["resources"]
    assert isinstance(resources, list)
    removed = resources.pop()
    assert isinstance(removed, dict)
    approved["resource_count"] = len(resources)

    report = verify_packaged_contract_bundle_manifest(approved)

    assert report.verified is False
    assert report.mismatches == (
        f"resource_missing:{removed['resource_path']}",
    )


def test_unexpected_resource_fails_closed() -> None:
    """An approved manifest cannot silently authorize unpublished resources."""
    approved = _approved_manifest()
    resources = approved["resources"]
    assert isinstance(resources, list)
    resources.append(
        {
            "resource_path": "schemas/unpublished.v1.schema.json",
            "sha256": "1" * 64,
        }
    )
    approved["resource_count"] = len(resources)

    report = verify_packaged_contract_bundle_manifest(approved)

    assert report.verified is False
    assert report.mismatches == (
        "resource_unexpected:schemas/unpublished.v1.schema.json",
    )


@pytest.mark.parametrize("bad_count", [999, 17.0, True])
def test_resource_count_must_exactly_match_resource_list(bad_count: object) -> None:
    """Count metadata cannot misstate or weakly type approved evidence."""
    approved = _approved_manifest()
    approved["resource_count"] = bad_count

    report = verify_packaged_contract_bundle_manifest(approved)

    assert report.verified is False
    assert report.mismatches == ("resource_count",)


def test_non_mapping_bundle_manifest_fails_closed() -> None:
    """The public verifier rejects a non-object approved manifest."""
    report = verify_packaged_contract_bundle_manifest([])

    assert report.verified is False
    assert report.mismatches == ("manifest",)


@pytest.mark.parametrize(
    "resources",
    [
        "not-a-list",
        [None],
        [{"resource_path": 7, "sha256": "0" * 64}],
        [{"resource_path": "schemas/a.json", "sha256": 7}],
        [
            {"resource_path": "schemas/a.json", "sha256": "0" * 64},
            {"resource_path": "schemas/a.json", "sha256": "1" * 64},
        ],
    ],
)
def test_malformed_or_duplicate_resources_fail_closed(resources: object) -> None:
    """Malformed resource evidence cannot become package authorization."""
    approved = _approved_manifest()
    approved["resources"] = resources
    approved["resource_count"] = 1

    report = verify_packaged_contract_bundle_manifest(approved)

    assert report.verified is False
    assert "resources" in report.mismatches


def test_bundle_verifier_cli_is_installed_by_project_metadata() -> None:
    """Buyers receive exact bundle verification as an installed command."""
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["scripts"]["cwl-context-bundle-verify"] == (
        "cwl_context_contracts.contract_bundle_manifest_verifier:main"
    )


def test_bundle_verifier_cli_accepts_exact_manifest(tmp_path, capsys) -> None:
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


def test_bundle_verifier_cli_rejects_drift_with_nonzero_exit(
    tmp_path,
    capsys,
) -> None:
    """Automation gets exit one when approved and installed bytes diverge."""
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


def test_bundle_verifier_cli_rejects_invalid_input(tmp_path, capsys) -> None:
    """Unsafe input failures remain machine-readable and fail closed."""
    approved_path = tmp_path / "approved.json"
    approved_path.write_text("{", encoding="utf-8")

    exit_code = verifier_module.main([str(approved_path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload == {
        "verification_format": "cwl-context-bundle-verification/v1",
        "verified": False,
        "error": "approved_manifest_invalid_json",
        "next_action": "provide a readable approved contract bundle manifest JSON object",
    }
