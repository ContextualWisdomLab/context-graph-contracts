"""Regression tests for explicit hosted-runner image pinning."""

from pathlib import Path


WORKFLOW_DIR = Path(__file__).parents[1] / ".github" / "workflows"


def test_required_workflows_pin_supported_hosted_runner_image() -> None:
    """Required lanes must not depend on the floating hosted-runner alias."""
    offenders: list[str] = []
    for workflow_path in sorted(WORKFLOW_DIR.glob("*.yml")):
        workflow_text = workflow_path.read_text(encoding="utf-8")
        if "runs-on: ubuntu-latest" in workflow_text:
            offenders.append(workflow_path.name)

    assert offenders == [], (
        "floating ubuntu-latest runner aliases can remain queued before checkout; "
        f"pin an explicit supported image in: {', '.join(offenders)}"
    )
