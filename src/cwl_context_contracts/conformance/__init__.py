"""Packaged provider-neutral conformance profiles."""

from __future__ import annotations

import json
from hashlib import sha256
from importlib.resources import files
from typing import Any

_PROFILE_NAMES = (
    "cwl-timestamp-profile.v1.json",
    "context-assertion-semantics.v1.json",
    "cloudevent-semantics.v1.json",
    "cwl-json-interoperability.v1.json",
)


def available_conformance_profile_names() -> tuple[str, ...]:
    """Return packaged conformance profile names in stable order."""
    return _PROFILE_NAMES


def _profile_resource(name: str):
    """Return one validated packaged profile resource."""
    if name not in _PROFILE_NAMES:
        raise ValueError(f"unknown conformance profile: {name}")
    return files(__package__).joinpath(name)


def load_conformance_profile(name: str) -> dict[str, Any]:
    """Load one packaged conformance profile by exact file name."""
    text = _profile_resource(name).read_text(encoding="utf-8")
    return json.loads(text)


def conformance_profile_sha256(name: str) -> str:
    """Return the SHA-256 digest of one exact packaged profile byte sequence."""
    return sha256(_profile_resource(name).read_bytes()).hexdigest()
