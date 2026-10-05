"""Run a synthetic prerelease SDK sample, never release approval or authorization.

Use an installed package and an absolute script path from any working directory.
For a local prerelease package smoke environment, start in the checkout::

    checkout="$PWD"
    cd "$HOME"
    "$checkout/.package-smoke/bin/python" -I \\
        "$checkout/examples/context_assertion_quickstart.py"

The package must already be installed in that interpreter. No PYTHONPATH or
source import is needed. The positive event is a packaged semantic-profile
fixture, not fixtures/valid-event.json (which is a different event type).
Its evidence digest is synthetic; no real evidence bytes are verified here.
This example does not import owner services or persist facts in a graph store.
"""

import json

from cwl_context_contracts import (
    CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE,
    ContextAssertion,
    ContextAssertionAdmission,
    admit_context_assertion_message,
    load_conformance_profile,
)


def main() -> None:
    """Roundtrip an installed positive vector, preserving its observed truth."""
    profile = load_conformance_profile("context-assertion-event-semantics.v1.json")
    vector = next(
        item
        for item in profile["valid_vectors"]
        if item["case_id"] == "canonical_assertion_event"
    )
    event = vector["value"]
    admitted: ContextAssertionAdmission = admit_context_assertion_message(
        CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE, event
    )
    assertion: ContextAssertion = ContextAssertion.from_mapping(
        json.loads(json.dumps(admitted.assertion.to_mapping()))
    )
    envelope = admitted.envelope.to_mapping()
    readmitted = admit_context_assertion_message(
        CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE,
        json.loads(json.dumps(envelope)),
    )
    assert assertion == admitted.assertion == readmitted.assertion
    assert assertion.to_mapping() == event["data"]
    assert envelope == event == readmitted.envelope.to_mapping()

    # Negative sample only: foreign observed sources are allowed, but a foreign
    # source cannot claim an owner-controlled authoritative disposition.
    altered = json.loads(json.dumps(event))
    altered["data"]["truth_status"] = "authoritative"
    altered["source"] = "urn:cwl:tt:foreign_observer"
    try:
        admit_context_assertion_message(
            CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE, altered
        )
    except ValueError as error:
        rejections = {"altered_source_authority": str(error)}
    else:
        raise RuntimeError("Altered source authority was unexpectedly admitted")

    try:
        admit_context_assertion_message("application/json", event)
    except ValueError as error:
        rejections["invalid_media_type"] = str(error)
    else:
        raise RuntimeError("Invalid structured media type was unexpectedly admitted")

    print(
        json.dumps(
            {
                "fixture_case": vector["case_id"],
                "envelope": envelope,
                "assertion": assertion.to_mapping(),
                "roundtrip_preserved": True,
                "rejections": rejections,
                "sample_data": True,
                "compatibility_only": True,
                "release_verified": False,
                "runtime_authorized": False,
                "notice": "Synthetic sample; not release approval or authorization.",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
