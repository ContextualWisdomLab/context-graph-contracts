"""Package-workflow regressions for the structured-message admission profile."""

from pathlib import Path


def test_ci_packages_and_enumerates_message_admission_profile(repository_root: Path) -> None:
    """Keep wheel/sdist inventory and installed-profile smoke aligned with the SDK."""

    workflow = (repository_root / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert (
        '"cwl_context_contracts/conformance/'
        'context-assertion-message-admission.v1.json",'
    ) in workflow
    assert (
        '\n              "context-assertion-message-admission.v1.json",\n'
    ) in workflow
