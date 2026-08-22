"""Integrity manifest for the exact packaged Context Fabric contract resources."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib.metadata import version

# Python >=3.11 is the supported runtime contract.
from importlib.resources import files  # nosemgrep

from .conformance import available_conformance_profile_names
from .contracts import available_contract_names
from .fixtures import available_fixture_names
from .schemas import available_schema_names

_MANIFEST_FORMAT = "cwl-context-bundle-manifest/v1"
_DISTRIBUTION_NAME = "cwl-context-contracts"
_NEXT_ACTION = (
    "store this manifest with approved release evidence and verify semantic "
    "conformance, package provenance, and runtime authorization before enabling "
    "the integration"
)
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


@dataclass(frozen=True, slots=True)
class ContractResourceEvidence:
    """SHA-256 identity evidence for one exact packaged contract resource."""

    resource_path: str
    sha256: str

    def to_mapping(self) -> dict[str, str]:
        """Return the stable JSON-native resource evidence record."""
        return {
            "resource_path": self.resource_path,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class ContractBundleManifest:
    """Version-bound integrity evidence for all published contract resources."""

    distribution_name: str
    distribution_version: str
    resources: tuple[ContractResourceEvidence, ...]

    @property
    def resource_count(self) -> int:
        """Return the number of exact packaged resources bound by this manifest."""
        return len(self.resources)

    def to_mapping(self) -> dict[str, object]:
        """Return a deterministic machine-readable contract bundle manifest."""
        return {
            "manifest_format": _MANIFEST_FORMAT,
            "distribution_name": self.distribution_name,
            "distribution_version": self.distribution_version,
            "algorithm": "sha256",
            "resource_count": self.resource_count,
            "resources": [resource.to_mapping() for resource in self.resources],
            "next_action": _NEXT_ACTION,
        }


def _resource_evidence(
    directory_name: str,
    package_name: str,
    resource_name: str,
) -> ContractResourceEvidence:
    """Build digest evidence for one explicitly published package resource."""
    resource_bytes = files(package_name).joinpath(resource_name).read_bytes()
    return ContractResourceEvidence(
        resource_path=f"{directory_name}/{resource_name}",
        sha256=hashlib.sha256(resource_bytes).hexdigest(),
    )


def build_packaged_contract_bundle_manifest() -> ContractBundleManifest:
    """Bind every published JSON contract resource to this installed version."""
    resources = tuple(
        sorted(
            (
                _resource_evidence(directory_name, package_name, resource_name)
                for directory_name, package_name, name_reader in _RESOURCE_GROUPS
                for resource_name in name_reader()
            ),
            key=lambda resource: resource.resource_path,
        )
    )
    return ContractBundleManifest(
        distribution_name=_DISTRIBUTION_NAME,
        distribution_version=version(_DISTRIBUTION_NAME),
        resources=resources,
    )


def main() -> int:
    """Print the installed contract bundle manifest as deterministic JSON."""
    manifest = build_packaged_contract_bundle_manifest()
    print(json.dumps(manifest.to_mapping(), sort_keys=True))
    return 0
