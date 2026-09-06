"""Regression contracts for repository-owned GitHub workflow execution."""

from pathlib import Path

WORKFLOW_DIR = Path(__file__).parents[1] / ".github" / "workflows"
EXACT_SOURCE_SHA = "${{ github.event.pull_request.head.sha || github.sha }}"


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


def test_pull_request_workflows_checkout_and_verify_exact_source_head() -> None:
    """Prevent synthetic pull-request merge refs from masquerading as source evidence."""

    exact_ref = f"ref: {EXACT_SOURCE_SHA}"
    exact_expected_sha = f"EXPECTED_SHA: {EXACT_SOURCE_SHA}"
    exact_verification = 'run: test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"'

    for workflow_path in sorted(WORKFLOW_DIR.glob("*.yml")):
        workflow_text = workflow_path.read_text(encoding="utf-8")
        if "pull_request:" not in workflow_text:
            continue
        checkout_count = workflow_text.count("uses: actions/checkout@")
        assert checkout_count > 0, workflow_path.name
        assert workflow_text.count(exact_ref) == checkout_count, workflow_path.name
        assert workflow_text.count(exact_expected_sha) == checkout_count, workflow_path.name
        assert workflow_text.count(exact_verification) == checkout_count, workflow_path.name
