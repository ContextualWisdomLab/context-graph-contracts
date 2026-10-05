"""Exercise workflow shell boundaries on a reused self-hosted workspace."""

from __future__ import annotations

import os
import re
import subprocess
import textwrap
from pathlib import Path

_WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
_OUTPUTS = ("build-a", "build-b", "reproducibility-evidence")


def _steps(workflow: str, job: str) -> list[str]:
    """Extract actual YAML step blocks without interpreting workflow expressions."""
    source = (_WORKFLOWS / workflow).read_text(encoding="utf-8")
    job_body = source.split(f"  {job}:\n", 1)[1]
    job_body = re.split(r"(?m)^  [\w-]+:\n", job_body, maxsplit=1)[0]
    return re.split(r"(?m)^      - ", job_body.split("    steps:\n", 1)[1])[1:]


def _run_script(step: str) -> str:
    """Read the literal shell block from a workflow step."""
    match = re.search(r"(?m)^        run: \|\n((?:          .*\n|\n)+)", step)
    assert match is not None, "expected a literal workflow shell block"
    return textwrap.dedent(match.group(1))


def _initialization_script() -> str:
    """Extract the real filesystem initialization, excluding package execution."""
    for step in _steps("reproducibility.yml", "release-package-reproducibility"):
        if "run: |" not in step:
            continue
        script = _run_script(step)
        if re.search(r"(?m)^mkdir .*reproducibility-evidence$", script):
            # Before the fix, initialization shares a step with the verifier.
            # Execute its actual shell prefix, never stub Python, uv or Git.
            return script.split("\npython ", 1)[0]
    raise AssertionError("workflow has no reproducibility output initialization")


def _run_shell(script: str, workspace: Path) -> subprocess.CompletedProcess[str]:
    """Run the extracted block with GitHub's explicit Bash fail-fast flags."""
    return subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script],
        cwd=workspace,
        env={**os.environ, "GITHUB_WORKSPACE": str(workspace)},
        check=False,
        capture_output=True,
        text=True,
    )


def test_reproducibility_initialization_resets_only_owned_stale_outputs(
    tmp_path: Path,
) -> None:
    """Run actual YAML initialization twice over stale builds and evidence."""
    protected = ("source-a", "source-b", "unrelated-output")
    for name in (*_OUTPUTS, *protected):
        directory = tmp_path / name
        directory.mkdir()
        (directory / "keep-or-reset.txt").write_text("previous run", encoding="utf-8")
    steps = _steps("reproducibility.yml", "release-package-reproducibility")
    script = _initialization_script()
    initialization_index = next(
        index
        for index, step in enumerate(steps)
        if "run: |" in step and script.rstrip("\n") == _run_script(step).rstrip("\n")
    )
    build_indices = [index for index, step in enumerate(steps) if "uv build " in step]
    assert len(build_indices) == 2
    assert initialization_index < min(build_indices)
    verification = next(
        step
        for step in steps
        if "name: Verify byte-reproducible release packages" in step
    )
    assert "mkdir" not in _run_script(verification)

    for _ in range(2):
        result = _run_shell(script, tmp_path)
        assert result.returncode == 0, result.stderr
        for name in _OUTPUTS:
            directory = tmp_path / name
            assert directory.is_dir(), name
            assert list(directory.iterdir()) == [], f"stale output survived in {name}"
            (directory / "old.whl").write_bytes(b"stale output sentinel")
            nested = directory / "partial-build"
            nested.mkdir()
            (nested / "old.tar.gz").write_bytes(b"stale output sentinel")
        for name in protected:
            assert (tmp_path / name / "keep-or-reset.txt").read_text(
                encoding="utf-8"
            ) == "previous run"


def test_signing_checkout_is_explicitly_bound_before_repository_execution() -> None:
    """Require an exact ref and a fail-closed HEAD guard immediately after checkout."""
    steps = _steps("supply-chain.yml", "attest-protected-main")
    assert "uses: actions/checkout@" in steps[0]
    assert "ref: ${{ github.sha }}" in steps[0]
    assert "persist-credentials: false" in steps[0]
    guard = steps[1]
    assert "EXPECTED_SHA: ${{ github.sha }}" in guard
    script = _run_script(guard)
    assert "git rev-parse HEAD" in script
    assert '"$EXPECTED_SHA"' in script


def test_signing_head_guard_accepts_only_actual_checked_out_commit(
    tmp_path: Path,
) -> None:
    """Exercise the YAML HEAD guard using real local Git, not fabricated output."""
    guard = _steps("supply-chain.yml", "attest-protected-main")[1]
    script = _run_script(guard)
    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Workflow regression",
        "GIT_AUTHOR_EMAIL": "workflow-regression@example.invalid",
        "GIT_COMMITTER_NAME": "Workflow regression",
        "GIT_COMMITTER_EMAIL": "workflow-regression@example.invalid",
    }
    for args in (
        ["init", "--quiet"],
        ["commit", "--quiet", "--allow-empty", "-m", "fixture"],
    ):
        subprocess.run(["git", *args], cwd=tmp_path, env=git_env, check=True)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    for expected, exit_code in ((sha, 0), ("0" * 40, 1), ("", 1)):
        result = subprocess.run(
            ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script],
            cwd=tmp_path,
            env={**os.environ, "EXPECTED_SHA": expected},
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == exit_code, result.stderr
        if exit_code:
            assert "does not match the exact source SHA" in result.stderr
