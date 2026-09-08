"""Conformance-runner regressions for Context Assertion message-profile linkage."""

import cwl_context_contracts.conformance_runner as runner


def test_runner_rejects_message_profile_event_version_drift(monkeypatch) -> None:
    """Executable evidence must fail when the message profile links the wrong event version."""

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
