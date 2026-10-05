"""Regression contract for isolated self-hosted runner group selection."""

import re
from pathlib import Path

_WORKFLOW_DIRECTORY = Path(__file__).resolve().parents[2] / ".github" / "workflows"


def test_workflows_select_expected_self_hosted_runner_group() -> None:
    """Require dedicated CI and release mappings on every executable job."""
    workflow_paths = sorted(_WORKFLOW_DIRECTORY.glob("*.yml"))
    assert {path.name for path in workflow_paths} == {
        "ci.yml",
        "receipt-package-smoke.yml",
        "reproducibility.yml",
        "supply-chain.yml",
    }
    jobs_checked = 0
    for workflow_path in workflow_paths:
        source = workflow_path.read_text(encoding="utf-8")
        blocks = re.split(r"(?m)^  ([\w-]+):\n", source.split("jobs:\n", 1)[1])
        assert len(blocks) >= 3, workflow_path.name
        for index in range(1, len(blocks), 2):
            job, block = blocks[index : index + 2]
            expected_group = (
                "CWL contracts release"
                if job == "attest-protected-main"
                else "CWL contracts CI"
            )
            mappings = re.findall(
                r"(?m)^    runs-on:\n      group: ([^\n]+)\n"
                r"      labels: (\[[^\n]+\])$",
                block,
            )
            assert mappings == [(expected_group, "[self-hosted, Linux, X64, cwlab]")], (
                workflow_path.name,
                job,
            )
            jobs_checked += 1
    assert jobs_checked == 6
