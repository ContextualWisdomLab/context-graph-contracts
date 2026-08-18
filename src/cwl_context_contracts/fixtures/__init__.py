"""Packaged positive and negative conformance fixtures."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

_FIXTURE_NAMES = (
    "valid-event.json",
    "invalid-event.json",
    "valid-assertion.json",
    "invalid-assertion.json",
    "data-management-contract.valid.json",
    "data-management-assessment.valid.json",
)


def available_fixture_names() -> tuple[str, ...]:
    """Return packaged fixture names in stable positive/negative order."""
    return _FIXTURE_NAMES


def load_fixture(name: str) -> dict[str, Any]:
    """Load one packaged conformance fixture by exact file name."""
    if name not in _FIXTURE_NAMES:
        raise ValueError(f"unknown fixture name: {name}")
    text = files(__package__).joinpath(name).read_text(encoding="utf-8")
    return json.loads(text)
