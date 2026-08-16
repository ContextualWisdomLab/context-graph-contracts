"""Packaged provider-neutral conformance profiles."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

_PROFILE_NAMES = (
    "cwl-timestamp-profile.v1.json",
    "context-assertion-semantics.v1.json",
    "cwl-json-interoperability.v1.json",
)


def available_conformance_profile_names() -> tuple[str, ...]:
    """Return packaged conformance profile names in stable order."""
    return _PROFILE_NAMES


def load_conformance_profile(name: str) -> dict[str, Any]:
    """Load one packaged conformance profile by exact file name."""
    if name not in _PROFILE_NAMES:
        raise ValueError(f"unknown conformance profile: {name}")
    text = files(__package__).joinpath(name).read_text(encoding="utf-8")
    return json.loads(text)
