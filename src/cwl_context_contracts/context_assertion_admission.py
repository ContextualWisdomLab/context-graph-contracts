"""Transport-aware admission for packaged Context Assertion CloudEvents."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .assertion import ContextAssertion
from .events import CloudEventEnvelope

CONTEXT_ASSERTION_STRUCTURED_MEDIA_TYPE = "application/cloudevents+json"
_CONTEXT_ASSERTION_EVENT_PROFILE_ID = (
    "urn:cwl:context-contracts:context-assertion-event-semantics:v1"
)
_CONTEXT_ASSERTION_EVENT_PROFILE_VERSION = 1
_CONTEXT_ASSERTION_ADMISSION_VERSION = 1
_STRUCTURED_MEDIA_TYPE_PATTERN = re.compile(
    r'^\s*application/cloudevents\+json\s*'
    r'(?:;\s*charset\s*=\s*(?:"utf-8"|utf-8)\s*)?$',
    re.IGNORECASE | re.ASCII,
)


@dataclass(frozen=True, slots=True)
class ContextAssertionAdmission:
    """One admitted assertion plus the envelope and version evidence it arrived with."""

    envelope: CloudEventEnvelope
    assertion: ContextAssertion
    profile_id: str = field(default=_CONTEXT_ASSERTION_EVENT_PROFILE_ID, init=False)
    profile_version: int = field(
        default=_CONTEXT_ASSERTION_EVENT_PROFILE_VERSION,
        init=False,
    )
    admission_version: int = field(default=_CONTEXT_ASSERTION_ADMISSION_VERSION, init=False)

    def __post_init__(self) -> None:
        """Reject manually constructed receipts whose envelope and assertion disagree."""

        if type(self.envelope) is not CloudEventEnvelope:
            raise TypeError("envelope must be a CloudEventEnvelope")
        if type(self.assertion) is not ContextAssertion:
            raise TypeError("assertion must be a ContextAssertion")
        if ContextAssertion.from_event(self.envelope) != self.assertion:
            raise ValueError("assertion must match the admitted CloudEvent envelope")


def _is_context_assertion_structured_media_type(media_type: str) -> bool:
    """Accept the JSON structured media type and its UTF-8 HTTP variant."""

    return _STRUCTURED_MEDIA_TYPE_PATTERN.fullmatch(media_type) is not None


def admit_context_assertion_message(
    media_type: str,
    value: Mapping[str, Any],
) -> ContextAssertionAdmission:
    """Admit one structured message without discarding its event identity."""

    if not isinstance(media_type, str):
        raise TypeError("Context Assertion media type must be a string")
    if not _is_context_assertion_structured_media_type(media_type):
        raise ValueError(
            "Context Assertion media type must be application/cloudevents+json"
        )
    envelope = CloudEventEnvelope.from_mapping(value)
    assertion = ContextAssertion.from_event(envelope)
    return ContextAssertionAdmission(envelope=envelope, assertion=assertion)
