"""Transport-aware admission for packaged Context Assertion CloudEvents."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .assertion import ContextAssertion
from .events import CloudEventEnvelope

CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE = "application/cloudevents+json"


def admit_context_assertion_message(
    media_type: str,
    value: Mapping[str, Any],
) -> ContextAssertion:
    """Admit one Context Assertion only under its advertised structured media type."""

    if not isinstance(media_type, str):
        raise TypeError("Context Assertion media type must be a string")
    if media_type != CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE:
        raise ValueError(
            "Context Assertion media type must be application/cloudevents+json"
        )
    event = CloudEventEnvelope.from_mapping(value)
    return ContextAssertion.from_event(event)
