"""Conformance-runner regressions for Context Assertion message-profile linkage."""

import pytest

import cwl_context_contracts.conformance_runner as runner


def test_runner_rejects_message_profile_event_version_drift(monkeypatch) -> None:
    """Fail evidence when the message profile links the wrong event version."""

    original_load = runner.load_conformance_profile

    def load_profile(name: str):
        profile = original_load(name)
        if name == "context-assertion-message-admission.v1.json":
            profile["event_profile_version"] = 2
        return profile

    monkeypatch.setattr(runner, "load_conformance_profile", load_profile)

    report = runner.run_packaged_conformance()

    failure = next(
        item
        for item in report.failures
        if item.profile_name == "context-assertion-message-admission.v1.json"
    )
    assert failure.case_id == "event_profile_link"
    assert "version" in failure.detail


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "profile_id",
            "urn:cwl:context-contracts:context-assertion-message-admission:v2",
        ),
        ("profile_version", 2),
        ("structured_media_type", "application/json"),
    ],
)
def test_runner_rejects_message_profile_identity_drift(
    monkeypatch,
    field: str,
    value: object,
) -> None:
    """Executable evidence must bind the message profile's own v1 identity."""

    original_load = runner.load_conformance_profile

    def load_profile(name: str):
        profile = original_load(name)
        if name == "context-assertion-message-admission.v1.json":
            profile[field] = value
        return profile

    monkeypatch.setattr(runner, "load_conformance_profile", load_profile)

    report = runner.run_packaged_conformance()

    failure = next(
        item
        for item in report.failures
        if item.profile_name == "context-assertion-message-admission.v1.json"
    )
    assert failure.case_id == "message_profile_identity"
    assert "message admission profile" in failure.detail


def test_runner_reports_invalid_message_vector_that_admission_accepts(
    monkeypatch,
) -> None:
    """An invalid media-type vector accepted by the SDK is explicit drift."""
    monkeypatch.setattr(
        runner,
        "admit_context_assertion_message",
        lambda _media_type, _event: None,
    )

    report = runner.run_packaged_conformance()

    failures = [
        item
        for item in report.failures
        if item.profile_name == "context-assertion-message-admission.v1.json"
    ]
    assert failures
    assert all("unexpectedly accepted" in item.detail for item in failures)
