"""Packaged JSON Schema resources."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

_SCHEMA_NAMES = (
    "canonical-authority-uri.schema.json",
    "canonical-asset-uri.schema.json",
    "truth-status.schema.json",
    "bitemporal-interval.schema.json",
    "provenance-reference.schema.json",
    "cloudevent-envelope.schema.json",
    "context-membership.schema.json",
    "context-assertion.schema.json",
    "data-management-framework.schema.json",
    "data-management-assessment.schema.json",
)


def available_schema_names() -> tuple[str, ...]:
    """Return packaged schema names in stable dependency order."""
    return _SCHEMA_NAMES


def load_schema(name: str) -> dict[str, Any]:
    """Load one packaged JSON Schema by exact file name."""
    if name not in _SCHEMA_NAMES:
        raise ValueError(f"unknown schema name: {name}")
    text = files(__package__).joinpath(name).read_text(encoding="utf-8")
    return json.loads(text)
