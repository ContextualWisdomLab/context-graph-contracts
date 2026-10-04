"""Check repository-owned CI isolation without admitting release authority."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
FORK_GUARD = (
    "github.event_name != 'pull_request' || "
    "github.event.pull_request.head.repo.full_name == github.repository"
)


def _jobs() -> list[tuple[str, str, str]]:
    """Read each executable job block from the reviewed workflow inventory."""
    result = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        source = path.read_text(encoding="utf-8")
        blocks = re.split(r"(?m)^  ([\w-]+):\n", source.split("jobs:\n", 1)[1])
        result.extend(
            (path.name, blocks[index], blocks[index + 1])
            for index in range(1, len(blocks), 2)
        )
    return result


def test_all_executable_jobs_use_dedicated_self_hosted_groups() -> None:
    """Keep every lane off hosted and unrelated privileged runner pools."""
    jobs = _jobs()
    assert len(jobs) == 6
    for workflow, name, block in jobs:
        group = "CWL contracts release" if name == "attest-protected-main" else (
            "CWL contracts CI"
        )
        assert f"group: {group}\n" in block, (workflow, name)
        assert "labels: [self-hosted, Linux, X64, cwlab]" in block, (workflow, name)
        assert re.search(r"(?m)^    runs-on:\n", block), (workflow, name)
        assert re.search(r"(?m)^    timeout-minutes: (10|20|30)$", block)
        if name != "attest-protected-main":
            assert FORK_GUARD in block, (workflow, name)


def test_privileged_release_is_separately_approved_and_explicitly_enabled() -> None:
    """Routing to a runner does not itself authorize OIDC-backed signing."""
    release = next(
        block for _, name, block in _jobs() if name == "attest-protected-main"
    )
    assert "github.event_name == 'push'" in release
    assert "github.ref == 'refs/heads/main'" in release
    assert "github.ref_protected" in release
    assert "vars.CONTRACTS_SELF_HOSTED_RELEASE_ENABLED == 'true'" in release
    assert "environment: contracts-release" in release
    assert "EXPECTED_RUNNER_ENVIRONMENT: self-hosted" in release
    assert "--deny-self-hosted-runners" not in release


def test_workflows_keep_pins_read_only_defaults_and_safe_checkout() -> None:
    """Preserve exact source identity, pins and least-privilege job defaults."""
    for path in sorted(WORKFLOWS.glob("*.yml")):
        source = path.read_text(encoding="utf-8")
        assert "permissions:\n  contents: read\n" in source
        assert "concurrency:" in source
        assert "defaults:\n  run:\n    shell: bash" in source
        assert "pull_request_target:" not in source
        assert "continue-on-error:" not in source
        for use in re.findall(r"(?m)^\s+uses: (\S+)", source):
            assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", use), use
        assert source.count("persist-credentials: false") == source.count(
            "uses: actions/checkout@"
        )


def test_smoke_evidence_uses_job_private_temporary_directories() -> None:
    """Avoid cross-job overwrite and stale receipts on persistent runner hosts."""
    for name in ("ci.yml", "receipt-package-smoke.yml"):
        source = (WORKFLOWS / name).read_text(encoding="utf-8")
        assert "/tmp/" not in source
        assert 'mktemp -d "${RUNNER_TEMP:?}/contracts-smoke.XXXXXX"' in source
        assert 'trap \'rm -rf -- "$SMOKE_ROOT"\' EXIT' in source
        assert 'Path(os.environ["SMOKE_ROOT"])' in source


def test_actions_helpers_and_tests_stay_under_github() -> None:
    """CI process helpers belong with workflows rather than application code."""
    assert not (ROOT / "scripts").exists()
    assert len(list((ROOT / ".github" / "scripts").glob("*"))) >= 4
    for path in sorted(WORKFLOWS.glob("*.yml")):
        source = path.read_text(encoding="utf-8")
        assert not re.search(r"(?<![\w./])scripts/", source)
    assert 'testpaths = ["tests", ".github/tests"]' in (
        ROOT / "pyproject.toml"
    ).read_text(encoding="utf-8")
