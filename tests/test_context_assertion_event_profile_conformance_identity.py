"""Conformance-runner regressions for Context Assertion event-profile identity."""

import pytest

import cwl_context_contracts.conformance_runner as runner


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "profile_id",
            "urn:cwl:context-contracts:context-assertion-event-semantics:v2",
        ),
        ("profile_version", 2),
    ],
)
def test_runner_rejects_event_profile_identity_drift(
    monkeypatch,
    field: str,
    value: object,
) -> None:
    """Executable evidence must bind the event profile's own v1 identity."""

    original_load = runner.load_conformance_profile

    def load_profile(name: str):
        profile = original_load(name)
        if name == "context-assertion-event-semantics.v1.json":
            profile[field] = value
        return profile

    monkeypatch.setattr(runner, "load_conformance_profile", load_profile)

    report = runner.run_packaged_conformance()

    failure = next(
        item
        for item in report.failures
        if item.profile_name == "context-assertion-event-semantics.v1.json"
    )
    assert failure.case_id == "event_profile_identity"
    assert "event profile" in failure.detail
