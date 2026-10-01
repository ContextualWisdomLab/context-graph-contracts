"""Regression contract for GitHub-hosted runner image selection."""

from pathlib import Path

_WORKFLOW_DIRECTORY = Path(__file__).parents[1] / ".github" / "workflows"


def test_hosted_workflows_pin_supported_runner_image() -> None:
    """Require every workflow to pin the supported hosted image."""
    offenders: list[str] = []
    for workflow_path in sorted(_WORKFLOW_DIRECTORY.glob("*.yml")):
        labels = [
            line.split(":", 1)[1].strip().split()[0]
            for line in workflow_path.read_text(encoding="utf-8").splitlines()
            if line.lstrip().startswith("runs-on:")
        ]
        if not labels or set(labels) != {"ubuntu-24.04"}:
            observed = ",".join(labels) if labels else "missing"
            offenders.append(f"{workflow_path.name}:{observed}")

    assert offenders == [], (
        "workflows must pin every hosted lane to ubuntu-24.04; "
        f"observed: {', '.join(offenders)}"
    )
