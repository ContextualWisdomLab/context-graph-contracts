"""Buyer acceptance for exact package checksum and SPDX evidence verification."""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

import pytest

import cwl_context_contracts
from cwl_context_contracts import package_evidence_verifier as verifier_module


_WHEEL_NAME = "cwl_context_contracts-0.1.0-py3-none-any.whl"
_SDIST_NAME = "cwl_context_contracts-0.1.0.tar.gz"
_SBOM_NAME = "cwl-context-contracts.spdx.json"
_SPDX_CONTEXT = "https://spdx.org/rdf/3.0.1/spdx-context.jsonld"


def _sha256(payload: bytes) -> str:
    """Return the lowercase SHA-256 digest used by the package workflow."""
    return hashlib.sha256(payload).hexdigest()


def _valid_spdx() -> bytes:
    """Return the smallest SPDX 3.0.1 document accepted by the workflow contract."""
    return json.dumps(
        {
            "@context": _SPDX_CONTEXT,
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


def _write_checksums(directory: Path, names: tuple[str, ...]) -> None:
    """Write checksums for the named files using the workflow's GNU format."""
    lines = []
    for name in names:
        payload = (directory / name).read_bytes()
        lines.append(f"{_sha256(payload)}  {name}\n")
    (directory / "SHA256SUMS").write_text("".join(lines), encoding="utf-8")


def _write_valid_evidence(directory: Path) -> dict[str, bytes]:
    """Write one realistic supply-chain evidence bundle and return its payloads."""
    payloads = {
        _WHEEL_NAME: b"wheel-bytes",
        _SDIST_NAME: b"sdist-bytes",
        _SBOM_NAME: _valid_spdx(),
    }
    for name, payload in payloads.items():
        (directory / name).write_bytes(payload)
    _write_checksums(directory, tuple(payloads))
    return payloads


def _replace_sbom(directory: Path, payload: object | bytes) -> None:
    """Replace the SBOM and refresh checksums so only SPDX semantics can fail."""
    encoded = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    (directory / _SBOM_NAME).write_bytes(encoded)
    _write_checksums(directory, (_WHEEL_NAME, _SDIST_NAME, _SBOM_NAME))


def test_exact_package_evidence_passes_with_machine_readable_artifact_identity(
    tmp_path: Path,
) -> None:
    """Exact wheel, sdist, SPDX and checksum evidence produces a positive decision."""
    payloads = _write_valid_evidence(tmp_path)

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is True
    assert report.mismatches == ()
    assert report.to_mapping()["verification_format"] == (
        "cwl-context-package-evidence-verification/v1"
    )
    assert report.to_mapping()["artifacts"] == [
        {"name": name, "sha256": _sha256(payloads[name])}
        for name in sorted(payloads)
    ]
    assert report.next_action == (
        "verify artifact attestations bind these exact package bytes to the intended "
        "protected main source commit before release"
    )


def test_tampered_artifact_fails_without_relabeling_checksum_evidence(
    tmp_path: Path,
) -> None:
    """A post-build byte change is rejected when SHA256SUMS remains unchanged."""
    _write_valid_evidence(tmp_path)
    (tmp_path / _WHEEL_NAME).write_bytes(b"tampered-wheel")

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == (f"artifact_sha256:{_WHEEL_NAME}",)
    assert report.next_action == (
        "rebuild or reacquire exact package evidence before provenance and release "
        "verification"
    )


def test_checksum_manifest_must_cover_exact_release_artifact_kinds(
    tmp_path: Path,
) -> None:
    """The evidence set cannot omit the sdist or canonical SPDX document."""
    payloads = _write_valid_evidence(tmp_path)
    (tmp_path / "SHA256SUMS").write_text(
        f"{_sha256(payloads[_WHEEL_NAME])}  {_WHEEL_NAME}\n",
        encoding="utf-8",
    )

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("artifact_set",)


def test_checksum_manifest_rejects_path_traversal(tmp_path: Path) -> None:
    """A checksum entry cannot escape the supplied evidence directory."""
    _write_valid_evidence(tmp_path)
    digest = "0" * 64
    (tmp_path / "SHA256SUMS").write_text(
        f"{digest}  ../escape.whl\n",
        encoding="utf-8",
    )

    with pytest.raises(verifier_module.PackageEvidenceInputError) as exc_info:
        cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert exc_info.value.error_code == "checksum_manifest_invalid"


def test_checksum_manifest_rejects_duplicate_artifact_identity(tmp_path: Path) -> None:
    """Two checksum rows cannot claim the same package artifact identity."""
    _write_valid_evidence(tmp_path)
    digest = "0" * 64
    (tmp_path / "SHA256SUMS").write_text(
        f"{digest}  {_WHEEL_NAME}\n{digest}  {_WHEEL_NAME}\n",
        encoding="utf-8",
    )

    with pytest.raises(verifier_module.PackageEvidenceInputError) as exc_info:
        cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert exc_info.value.error_code == "checksum_manifest_invalid"


def test_empty_checksum_manifest_is_invalid(tmp_path: Path) -> None:
    """An empty checksum manifest cannot become positive release evidence."""
    _write_valid_evidence(tmp_path)
    (tmp_path / "SHA256SUMS").write_text("", encoding="utf-8")

    with pytest.raises(verifier_module.PackageEvidenceInputError) as exc_info:
        cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert exc_info.value.error_code == "checksum_manifest_invalid"


def test_unreadable_checksum_manifest_has_distinct_input_error(tmp_path: Path) -> None:
    """A non-file SHA256SUMS path is reported as unreadable input."""
    _write_valid_evidence(tmp_path)
    (tmp_path / "SHA256SUMS").unlink()
    (tmp_path / "SHA256SUMS").mkdir()

    with pytest.raises(verifier_module.PackageEvidenceInputError) as exc_info:
        cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert exc_info.value.error_code == "checksum_manifest_unreadable"


def test_symlinked_package_artifact_is_not_followed(tmp_path: Path) -> None:
    """Verification refuses a symlink substitution outside the evidence bundle."""
    payloads = _write_valid_evidence(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-wheel"
    outside.write_bytes(payloads[_WHEEL_NAME])
    (tmp_path / _WHEEL_NAME).unlink()
    (tmp_path / _WHEEL_NAME).symlink_to(outside)

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == (f"artifact_unsafe:{_WHEEL_NAME}",)


def test_missing_package_artifact_is_unsafe(tmp_path: Path) -> None:
    """A checksum cannot make a missing package artifact acceptable."""
    _write_valid_evidence(tmp_path)
    (tmp_path / _SDIST_NAME).unlink()

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == (f"artifact_unsafe:{_SDIST_NAME}",)


def test_symlinked_sbom_is_not_parsed_or_followed(tmp_path: Path) -> None:
    """The canonical SPDX evidence file is also restricted to a regular file."""
    payloads = _write_valid_evidence(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-sbom"
    outside.write_bytes(payloads[_SBOM_NAME])
    (tmp_path / _SBOM_NAME).unlink()
    (tmp_path / _SBOM_NAME).symlink_to(outside)

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == (f"artifact_unsafe:{_SBOM_NAME}",)


@pytest.mark.parametrize(
    "invalid_sbom",
    [
        b"{",
        [],
        {"@context": "https://example.invalid/spdx", "@graph": []},
        {"@context": _SPDX_CONTEXT, "@graph": {}},
        {"@context": _SPDX_CONTEXT, "@graph": []},
        {
            "@context": _SPDX_CONTEXT,
            "@graph": ["noise", {"type": "software_Package"}],
        },
        {
            "@context": _SPDX_CONTEXT,
            "@graph": [{"type": "CreationInfo", "specVersion": "3.0.1"}],
        },
    ],
)
def test_spdx_document_must_preserve_3_0_1_package_evidence_shape(
    tmp_path: Path,
    invalid_sbom: object | bytes,
) -> None:
    """Checksum equality cannot hide malformed or wrong-version SPDX evidence."""
    _write_valid_evidence(tmp_path)
    _replace_sbom(tmp_path, invalid_sbom)

    report = cwl_context_contracts.verify_package_evidence_directory(tmp_path)

    assert report.verified is False
    assert report.mismatches == ("sbom_spdx_3_0_1",)


def test_package_evidence_cli_emits_deterministic_success(
    tmp_path: Path,
    capsys,
) -> None:
    """Operators receive one JSON decision and exit zero for exact package evidence."""
    _write_valid_evidence(tmp_path)

    exit_code = verifier_module.main([str(tmp_path)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["verified"] is True
    assert payload["mismatches"] == []
    assert captured.err == ""


def test_package_evidence_cli_returns_exit_one_for_digest_drift(
    tmp_path: Path,
    capsys,
) -> None:
    """A verification mismatch is distinct from malformed operator input."""
    _write_valid_evidence(tmp_path)
    (tmp_path / _WHEEL_NAME).write_bytes(b"tampered-wheel")

    exit_code = verifier_module.main([str(tmp_path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["verified"] is False
    assert payload["mismatches"] == [f"artifact_sha256:{_WHEEL_NAME}"]


def test_package_evidence_cli_fails_closed_on_missing_directory(
    tmp_path: Path,
    capsys,
) -> None:
    """Unreadable evidence input returns a distinct operator-fixable exit code."""
    missing = tmp_path / "missing"

    exit_code = verifier_module.main([str(missing)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload == {
        "verification_format": "cwl-context-package-evidence-verification/v1",
        "verified": False,
        "error": "evidence_directory_unreadable",
        "next_action": "provide a readable package-evidence directory",
    }


def test_package_evidence_cli_is_installed_by_project_metadata() -> None:
    """Release operators receive the verifier in the built distribution."""
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["scripts"]["cwl-context-package-evidence-verify"] == (
        "cwl_context_contracts.package_evidence_verifier:main"
    )
