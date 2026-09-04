"""Installed entry-point acceptance for semantic conformance evidence."""

from importlib.metadata import entry_points

import cwl_context_contracts.conformance_runner as runner


def test_conformance_console_script_resolves_to_reference_runner() -> None:
    """The installed project exposes the documented fail-closed console command."""
    matches = [
        point
        for point in entry_points(group="console_scripts")
        if point.name == "cwl-context-conformance"
    ]

    assert len(matches) == 1
    assert matches[0].value == "cwl_context_contracts.conformance_runner:main"
    assert matches[0].load() is runner.main
