"""Transport-aware admission for packaged Context Assertion CloudEvents."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .assertion import ContextAssertion
from .events import CloudEventEnvelope

CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE = "application/cloudevents+json"
_STRUCTURED_MEDIA_TYPE_PATTERN = re.compile(
    r'^\s*application/cloudevents\+json\s*'
    r'(?:;\s*charset\s*=\s*(?:"utf-8"|utf-8)\s*)?$',
    re.IGNORECASE | re.ASCII,
)


def _is_context_assertion_structured_media_type(media_type: str) -> bool:
    """Accept the JSON structured media type and its UTF-8 HTTP variant."""

    return _STRUCTURED_MEDIA_TYPE_PATTERN.fullmatch(media_type) is not None


def admit_context_assertion_message(
    media_type: str,
    value: Mapping[str, Any],
) -> ContextAssertion:
    """Admit one Context Assertion under its CloudEvents structured media type."""

    if not isinstance(media_type, str):
        raise TypeError("Context Assertion media type must be a string")
    if not _is_context_assertion_structured_media_type(media_type):
        raise ValueError(
            "Context Assertion media type must be application/cloudevents+json"
        )
    event = CloudEventEnvelope.from_mapping(value)
    return ContextAssertion.from_event(event)
