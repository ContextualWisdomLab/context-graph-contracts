"""Regression contract for installed Context Assertion SDK smoke coverage."""

from pathlib import Path


_RECEIPT_SMOKE = Path(".github/workflows/receipt-package-smoke.yml")
_REQUIRED_INSTALLED_SDK_MARKERS = (
    "CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE",
    "ContextAssertionAdmission",
    "admit_context_assertion_message",
    "load_conformance_profile(",
    "context-assertion-event-semantics.v1.json",
    "admission.envelope.to_mapping() == event_mapping",
    "admission.assertion.to_mapping() == event_mapping[\"data\"]",
    "admission.profile_id",
    "admission.profile_version",
    "admission.admission_version",
)


def test_installed_wheel_smoke_exercises_context_assertion_admission_surface() -> None:
    """Require packaged SDK behavior, not source-tree-only admission coverage."""

    workflow = _RECEIPT_SMOKE.read_text(encoding="utf-8")
    assert ".receipt-smoke/bin/python" in workflow
    for marker in _REQUIRED_INSTALLED_SDK_MARKERS:
        assert marker in workflow, (
            "installed-wheel smoke must exercise Context Assertion admission marker: "
            f"{marker}"
        )
