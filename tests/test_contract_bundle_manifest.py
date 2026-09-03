"""Buyer acceptance for exact packaged contract-resource evidence."""

from __future__ import annotations

import hashlib
import importlib
import json
from importlib.metadata import version
from importlib.resources import files

from cwl_context_contracts import (
    available_conformance_profile_names,
    available_contract_names,
    available_fixture_names,
    available_schema_names,
    build_packaged_contract_bundle_manifest,
)

_DISTRIBUTION_NAME = "cwl-context-contracts"
_RESOURCE_GROUPS = (
    ("contracts", "cwl_context_contracts.contracts", available_contract_names),
    ("schemas", "cwl_context_contracts.schemas", available_schema_names),
    ("fixtures", "cwl_context_contracts.fixtures", available_fixture_names),
    (
        "conformance",
        "cwl_context_contracts.conformance",
        available_conformance_profile_names,
    ),
)


def _expected_resource_bytes() -> dict[str, bytes]:
    """Return every buyer-relevant packaged JSON resource by stable path."""
    expected: dict[str, bytes] = {}
    for directory_name, package_name, name_reader in _RESOURCE_GROUPS:
        for resource_name in name_reader():
            resource_path = f"{directory_name}/{resource_name}"
            expected[resource_path] = (
                files(package_name).joinpath(resource_name).read_bytes()
            )
    return expected


def test_bundle_manifest_binds_every_packaged_contract_resource() -> None:
    """Schema, AsyncAPI, fixture, and semantic bytes share one release identity."""
    manifest = build_packaged_contract_bundle_manifest()
    expected = _expected_resource_bytes()

    assert manifest.distribution_name == _DISTRIBUTION_NAME
    assert manifest.distribution_version == version(_DISTRIBUTION_NAME)
    assert manifest.resource_count == len(expected) == 17
    assert [item.resource_path for item in manifest.resources] == sorted(expected)
    for item in manifest.resources:
        assert item.sha256 == hashlib.sha256(expected[item.resource_path]).hexdigest()


def test_bundle_manifest_mapping_is_deterministic_and_actionable() -> None:
    """Operators receive stable evidence plus the next release-admission action."""
    mapping = build_packaged_contract_bundle_manifest().to_mapping()

    assert mapping["manifest_format"] == "cwl-context-bundle-manifest/v1"
    assert mapping["algorithm"] == "sha256"
    assert mapping["resource_count"] == 17
    assert mapping["next_action"] == (
        "store this manifest with approved release evidence and verify semantic "
        "conformance, package provenance, and runtime authorization before enabling "
        "the integration"
    )
    assert mapping["resources"] == sorted(
        mapping["resources"],
        key=lambda item: item["resource_path"],
    )


def test_bundle_manifest_cli_emits_exact_deterministic_json(capsys) -> None:
    """The installed command emits the same mapping consumed by automation."""
    expected = build_packaged_contract_bundle_manifest().to_mapping()
    module = importlib.import_module("cwl_context_contracts.contract_bundle_manifest")

    assert module.main() == 0
    captured = capsys.readouterr()

    assert json.loads(captured.out) == expected
    assert captured.out == json.dumps(expected, sort_keys=True) + "\n"
