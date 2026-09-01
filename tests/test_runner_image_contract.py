"""Regression contract for GitHub-hosted runner image selection."""

from pathlib import Path
import re

import pytest


WORKFLOW_PATHS = (
    Path(".github/workflows/ci.yml"),
    Path(".github/workflows/receipt-package-smoke.yml"),
    Path(".github/workflows/reproducibility.yml"),
    Path(".github/workflows/supply-chain.yml"),
)
RUNS_ON = re.compile(r"^\s*runs-on:\s*([^\s#]+)", re.MULTILINE)


@pytest.mark.parametrize("workflow_path", WORKFLOW_PATHS)
def test_hosted_workflows_pin_supported_runner_image(workflow_path: Path) -> None:
    """Require an explicit hosted image instead of the starving latest alias."""
    labels = RUNS_ON.findall(workflow_path.read_text(encoding="utf-8"))
    assert labels, f"{workflow_path} must declare at least one runs-on label"
    assert set(labels) == {"ubuntu-24.04"}, (
        f"{workflow_path} must pin ubuntu-24.04; observed runner labels: {labels}"
    )
