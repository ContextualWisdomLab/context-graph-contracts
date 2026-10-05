"""Exercise the SDK quickstart as an isolated executable outside the checkout."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from cwl_context_contracts import load_conformance_profile

_SCRIPT = (
    Path(__file__).resolve().parents[1] / "examples/context_assertion_quickstart.py"
)


def _run_quickstart(cwd: Path) -> dict[str, Any]:
    """Run the real script without source-path injection and decode its one line."""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-I", str(_SCRIPT)],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert len(result.stdout.splitlines()) == 1
    output = json.loads(result.stdout)
    assert result.stdout.strip() == json.dumps(
        output, sort_keys=True, separators=(",", ":")
    )
    return output


def test_quickstart_labels_sample_as_compatibility_only(tmp_path: Path) -> None:
    """Do not confuse executable synthetic sample data with release approval."""
    output = _run_quickstart(tmp_path)

    assert output["sample_data"] is True
    assert output["compatibility_only"] is True
    assert output["release_verified"] is False
    assert output["runtime_authorized"] is False
    assert (
        output["notice"] == "Synthetic sample; not release approval or authorization."
    )


def test_quickstart_roundtrips_packaged_assertion_with_envelope(tmp_path: Path) -> None:
    """Keep truth, evidence, both time axes, and every membership unchanged."""
    output = _run_quickstart(tmp_path)
    profile = load_conformance_profile("context-assertion-event-semantics.v1.json")
    vector = next(
        item
        for item in profile["valid_vectors"]
        if item["case_id"] == "canonical_assertion_event"
    )
    event = vector["value"]

    assert output["fixture_case"] == vector["case_id"]
    assert output["envelope"] == event
    assert output["assertion"] == event["data"]
    assert output["assertion"]["truth_status"] == "observed"
    assert (
        output["assertion"]["interval"]["valid_from"]
        != (output["assertion"]["interval"]["recorded_at"])
    )
    assert output["assertion"]["memberships"]
    assert output["roundtrip_preserved"] is True


def test_quickstart_rejects_forged_owner_authority(tmp_path: Path) -> None:
    """Show a foreign producer cannot relabel sample evidence as owner truth."""
    output = _run_quickstart(tmp_path)

    assert output["rejections"]["altered_source_authority"] == (
        "authoritative assertion source must own the assertion subject"
    )
    assert output["assertion"]["truth_status"] == "observed"


def test_quickstart_rejects_invalid_structured_media_type(tmp_path: Path) -> None:
    """Demonstrate transport admission rather than parsing bare JSON as an event."""
    output = _run_quickstart(tmp_path)

    assert output["rejections"]["invalid_media_type"] == (
        "Context Assertion media type must be application/cloudevents+json"
    )
