"""Machine-check the DDD ownership boundaries of the contract package."""

import ast
from pathlib import Path

_REQUIRED_DDD_DOCUMENTS = (
    "docs/CONTEXT_MAP.md",
    "docs/UBIQUITOUS_LANGUAGE.md",
    "docs/product-technical-gap-baseline.md",
)
_FORBIDDEN_GENERIC_DIRECTORIES = {
    "common",
    "core",
    "helpers",
    "legacy",
    "lib",
    "misc",
    "models",
    "services",
    "shared",
    "utils",
}
_FOREIGN_PRODUCT_PACKAGES = {
    "contextual_orchestrator",
    "ea_core_foundation",
    "enterprise_architecture_core",
    "lineageweave",
    "naruon",
    "pg_erd_cloud",
    "semantic_data_portal",
}


def test_canonical_ddd_documents_exist() -> None:
    """Keep bounded-context and language contracts in the executable baseline."""

    for relative_path in _REQUIRED_DDD_DOCUMENTS:
        path = Path(relative_path)
        assert path.is_file(), relative_path
        assert len(path.read_text(encoding="utf-8").strip()) >= 200, relative_path


def test_contract_package_does_not_grow_generic_domain_buckets() -> None:
    """Reject generic directories that can silently absorb unrelated behavior."""

    package_root = Path("src/cwl_context_contracts")
    offenders = sorted(
        str(path.relative_to(package_root))
        for path in package_root.rglob("*")
        if path.is_dir() and path.name in _FORBIDDEN_GENERIC_DIRECTORIES
    )
    assert offenders == []


def test_contract_package_does_not_import_foreign_product_implementations() -> None:
    """Keep product integrations at provider-neutral contract boundaries."""

    offenders: list[str] = []
    package_root = Path("src/cwl_context_contracts")
    for source_path in sorted(package_root.rglob("*.py")):
        tree = ast.parse(
            source_path.read_text(encoding="utf-8"),
            filename=str(source_path),
        )
        for node in ast.walk(tree):
            imported_roots: list[str] = []
            if isinstance(node, ast.Import):
                imported_roots.extend(
                    alias.name.split(".", 1)[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.append(node.module.split(".", 1)[0])
            for imported_root in imported_roots:
                if imported_root in _FOREIGN_PRODUCT_PACKAGES:
                    offenders.append(f"{source_path}:{imported_root}")
    assert offenders == []


def test_baseline_records_data_management_contract_boundary() -> None:
    """Keep the reference DTO surface from becoming a product system of record."""

    baseline = Path("docs/product-technical-gap-baseline.md").read_text(
        encoding="utf-8"
    )
    assert "src/cwl_context_contracts/data_management.py" in baseline
    assert "ADR 0013" in baseline
    assert "interoperability" in baseline.lower()
    assert "system of record" in baseline.lower()
