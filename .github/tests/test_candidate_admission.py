"""Exercise fail-closed candidate admission before self-hosted source checkout."""

from __future__ import annotations

import os
import re
import subprocess
import textwrap
from pathlib import Path

import pytest

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
REPOSITORY = "ContextualWisdomLab/context-graph-contracts"


def _candidate_steps() -> list[tuple[str, str]]:
    """Return each PR-capable job's actual pre-checkout admission step."""
    results = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        jobs = re.split(r"(?m)^  ([\w-]+):\n", path.read_text().split("jobs:\n", 1)[1])
        for index in range(1, len(jobs), 2):
            name, block = jobs[index : index + 2]
            if name == "attest-protected-main":
                continue
            assert not re.search(r"(?m)^    if:", block), (path.name, name)
            first = block.split("    steps:\n", 1)[1].split("      - ", 2)[1]
            assert first.startswith("name: Admit candidate before checkout\n"), name
            assert (
                "HEAD_REPOSITORY: "
                "${{ github.event.pull_request.head.repo.full_name }}" in first
            )
            match = re.search(r"(?m)^        run: \|\n((?:          .*\n|\n)+)", first)
            assert match is not None
            results.append((f"{path.name}:{name}", textwrap.dedent(match.group(1))))
    assert len(results) == 5
    return results


@pytest.mark.parametrize(
    ("event", "head", "exit_code"),
    [
        ("pull_request", REPOSITORY, 0),
        ("push", "", 0),
        ("pull_request", "outside/fork", 1),
        ("pull_request", "", 1),
        ("pull_request", "contextualwisdomlab/context-graph-contracts", 1),
        ("workflow_dispatch", REPOSITORY, 1),
    ],
)
def test_candidate_admission_rejects_unsupported_tuples_before_checkout(
    event: str, head: str, exit_code: int, tmp_path: Path,
) -> None:
    """Run actual admission Bash, without checkout or fake producer output."""
    for name, script in _candidate_steps():
        result = subprocess.run(
            ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script],
            cwd=tmp_path,
            env={
                **os.environ,
                "EVENT_NAME": event,
                "HEAD_REPOSITORY": head,
                "REPOSITORY": REPOSITORY,
            },
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == exit_code, (name, result.stderr)
        if exit_code:
            assert "unsupported candidate source" in result.stderr
        assert list(tmp_path.iterdir()) == []
