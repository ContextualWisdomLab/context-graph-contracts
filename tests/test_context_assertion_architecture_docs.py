"""Documentation fitness for the published Context Assertion event boundary."""

from pathlib import Path


def test_architecture_documents_complete_truth_and_event_semantics() -> None:
    """Keep the architecture guide aligned with executable assertion contracts."""

    architecture = Path("docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    for truth_status in (
        "authoritative",
        "observed",
        "inferred",
        "proposed",
        "superseded",
        "rejected",
    ):
        assert f"`{truth_status}`" in architecture

    required_semantics = (
        "application/cloudevents+json",
        "application/json",
        "ContextAssertionEvent",
        "admit_context_assertion_message",
        "outer",
        "enclosed",
        "id",
        "source",
        "specversion",
        "type",
        "time",
        "subject",
        "dataschema",
        "authoritative and observed assertions require provenance",
        "valid_from",
        "recorded_at",
    )
    for semantic in required_semantics:
        assert semantic in architecture
