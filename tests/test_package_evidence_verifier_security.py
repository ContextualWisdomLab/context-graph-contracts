"""Security regressions for package-evidence input ownership."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import cwl_context_contracts
import cwl_context_contracts.package_evidence_verifier as verifier_module
from cwl_context_contracts.package_evidence_verifier import PackageEvidenceInputError


def _digest(payload: bytes) -> str:
    """Return one workflow-compatible SHA-256 digest."""
    return hashlib.sha256(payload).hexdigest()


def test_symlinked_checksum_manifest_is_not_followed(tmp_path: Path) -> None:
    """A checksum authority outside the supplied evidence directory fails closed."""
    artifacts = {
        "cwl_context_contracts-0.1.0-py3-none-any.whl": b"wheel",
        "cwl_context_contracts-0.1.0.tar.gz": b"sdist",
        "cwl-context-contracts.spdx.json": json.dumps(
            {
                "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
                "@graph": [
                    {"type": "CreationInfo", "specVersion": "3.0.1"},
                    {"type": "software_Package"},
                ],
            }
        ).encode(),
    }
    for name, payload in artifacts.items():
        (tmp_path / name).write_bytes(payload)

    outside = tmp_path.parent / f"{tmp_path.name}-outside-sha256sums"
    outside.write_text(
        "".join(
            f"{_digest(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )
    (tmp_path / "SHA256SUMS").symlink_to(outside)

    with pytest.raises(PackageEvidenceInputError) as exc_info:
        cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert exc_info.value.error_code == "checksum_manifest_unsafe"


def test_spdx_package_identity_must_match_context_contract_distribution(
    tmp_path: Path,
) -> None:
    """Checksummed SPDX evidence for a different package cannot verify this release."""
    artifacts = {
        "cwl_context_contracts-0.1.0-py3-none-any.whl": b"wheel",
        "cwl_context_contracts-0.1.0.tar.gz": b"sdist",
        "cwl-context-contracts.spdx.json": json.dumps(
            {
                "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
                "@graph": [
                    {"type": "CreationInfo", "specVersion": "3.0.1"},
                    {"type": "software_Package", "name": "unrelated-package"},
                ],
            },
            sort_keys=True,
        ).encode(),
    }
    for name, payload in artifacts.items():
        (tmp_path / name).write_bytes(payload)
    (tmp_path / "SHA256SUMS").write_text(
        "".join(
            f"{_digest(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("sbom_spdx_3_0_1",)


def test_spdx_package_version_must_match_release_artifacts(tmp_path: Path) -> None:
    """Checksummed SPDX evidence for another release cannot verify these artifacts."""
    artifacts = {
        "cwl_context_contracts-0.1.0-py3-none-any.whl": b"wheel",
        "cwl_context_contracts-0.1.0.tar.gz": b"sdist",
        "cwl-context-contracts.spdx.json": json.dumps(
            {
                "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
                "@graph": [
                    {"type": "CreationInfo", "specVersion": "3.0.1"},
                    {
                        "type": "software_Package",
                        "name": "cwl-context-contracts",
                        "software_packageVersion": "9.9.9",
                    },
                ],
            },
            sort_keys=True,
        ).encode(),
    }
    for name, payload in artifacts.items():
        (tmp_path / name).write_bytes(payload)
    (tmp_path / "SHA256SUMS").write_text(
        "".join(
            f"{_digest(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("sbom_spdx_3_0_1",)


def test_package_artifact_names_must_match_context_contract_distribution(
    tmp_path: Path,
) -> None:
    """An unrelated wheel and sdist cannot borrow this product's SBOM identity."""
    artifacts = {
        "unrelated_package-9.9.9-py3-none-any.whl": b"wheel",
        "unrelated_package-9.9.9.tar.gz": b"sdist",
        "cwl-context-contracts.spdx.json": json.dumps(
            {
                "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
                "@graph": [
                    {"type": "CreationInfo", "specVersion": "3.0.1"},
                    {"type": "software_Package", "name": "cwl-context-contracts"},
                ],
            },
            sort_keys=True,
        ).encode(),
    }
    for name, payload in artifacts.items():
        (tmp_path / name).write_bytes(payload)
    (tmp_path / "SHA256SUMS").write_text(
        "".join(
            f"{_digest(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("artifact_set",)


def test_wheel_and_sdist_versions_must_match(tmp_path: Path) -> None:
    """Checksummed package formats from different releases cannot form one bundle."""
    artifacts = {
        "cwl_context_contracts-0.1.0-py3-none-any.whl": b"wheel",
        "cwl_context_contracts-0.2.0.tar.gz": b"sdist",
        "cwl-context-contracts.spdx.json": json.dumps(
            {
                "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
                "@graph": [
                    {"type": "CreationInfo", "specVersion": "3.0.1"},
                    {"type": "software_Package", "name": "cwl-context-contracts"},
                ],
            },
            sort_keys=True,
        ).encode(),
    }
    for name, payload in artifacts.items():
        (tmp_path / name).write_bytes(payload)
    (tmp_path / "SHA256SUMS").write_text(
        "".join(
            f"{_digest(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("artifact_set",)


def test_unlisted_installable_artifact_fails_closed(tmp_path: Path) -> None:
    """An unchecksummed wheel beside verified release files cannot inherit success."""
    artifacts = {
        "cwl_context_contracts-0.1.0-py3-none-any.whl": b"wheel",
        "cwl_context_contracts-0.1.0.tar.gz": b"sdist",
        "cwl-context-contracts.spdx.json": json.dumps(
            {
                "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
                "@graph": [
                    {"type": "CreationInfo", "specVersion": "3.0.1"},
                    {
                        "type": "software_Package",
                        "name": "cwl-context-contracts",
                        "software_packageVersion": "0.1.0",
                    },
                ],
            },
            sort_keys=True,
        ).encode(),
    }
    for name, payload in artifacts.items():
        (tmp_path / name).write_bytes(payload)
    (tmp_path / "SHA256SUMS").write_text(
        "".join(
            f"{_digest(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )
    (tmp_path / "cwl_context_contracts-9.9.9-py3-none-any.whl").write_bytes(
        b"unlisted-wheel"
    )

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("artifact_set",)


def test_unreadable_package_directory_listing_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A directory-listing failure becomes a stable verifier input error."""
    artifacts = {
        "cwl_context_contracts-0.1.0-py3-none-any.whl": b"wheel",
        "cwl_context_contracts-0.1.0.tar.gz": b"sdist",
        "cwl-context-contracts.spdx.json": json.dumps(
            {
                "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
                "@graph": [
                    {"type": "CreationInfo", "specVersion": "3.0.1"},
                    {
                        "type": "software_Package",
                        "name": "cwl-context-contracts",
                        "software_packageVersion": "0.1.0",
                    },
                ],
            },
            sort_keys=True,
        ).encode(),
    }
    for name, payload in artifacts.items():
        (tmp_path / name).write_bytes(payload)
    (tmp_path / "SHA256SUMS").write_text(
        "".join(
            f"{_digest(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )

    original_glob = Path.glob

    def unreadable_glob(path: Path, pattern: str):
        if path == tmp_path:
            raise OSError("directory listing failed")
        return original_glob(path, pattern)

    monkeypatch.setattr(Path, "glob", unreadable_glob)

    with pytest.raises(PackageEvidenceInputError) as exc_info:
        cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert exc_info.value.error_code == "evidence_directory_unreadable"


def test_spdx_semantics_use_the_same_bytes_that_passed_checksum_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Replacing the SBOM after hashing cannot splice two files into one success."""
    invalid_sbom = json.dumps(
        {
            "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
            "@graph": [
                {"type": "CreationInfo", "specVersion": "3.0.1"},
                {
                    "type": "software_Package",
                    "name": "unrelated-package",
                    "software_packageVersion": "0.1.0",
                },
            ],
        },
        sort_keys=True,
    ).encode()
    valid_sbom = json.dumps(
        {
            "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
            "@graph": [
                {"type": "CreationInfo", "specVersion": "3.0.1"},
                {
                    "type": "software_Package",
                    "name": "cwl-context-contracts",
                    "software_packageVersion": "0.1.0",
                },
            ],
        },
        sort_keys=True,
    ).encode()
    artifacts = {
        "cwl_context_contracts-0.1.0-py3-none-any.whl": b"wheel",
        "cwl_context_contracts-0.1.0.tar.gz": b"sdist",
        "cwl-context-contracts.spdx.json": invalid_sbom,
    }
    for name, payload in artifacts.items():
        (tmp_path / name).write_bytes(payload)
    (tmp_path / "SHA256SUMS").write_text(
        "".join(
            f"{_digest(payload)}  {name}\n" for name, payload in artifacts.items()
        ),
        encoding="utf-8",
    )

    original_sha256_file = verifier_module._sha256_file

    def replace_sbom_after_hash(path: Path) -> str:
        digest = original_sha256_file(path)
        if path.name == "cwl-context-contracts.spdx.json":
            path.write_bytes(valid_sbom)
        return digest

    monkeypatch.setattr(verifier_module, "_sha256_file", replace_sbom_after_hash)

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("sbom_spdx_3_0_1",)
