"""Packaged language-neutral interoperability contracts."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

_CONTRACT_NAMES = ("context-fabric.asyncapi.json",)


def available_contract_names() -> tuple[str, ...]:
    """Return packaged language-neutral contract names in stable order."""
    return _CONTRACT_NAMES


def load_contract(name: str) -> dict[str, Any]:
    """Load one packaged interoperability contract by exact file name."""
    if name not in _CONTRACT_NAMES:
        raise ValueError(f"unknown contract name: {name}")
    text = files(__package__).joinpath(name).read_text(encoding="utf-8")
    return json.loads(text)
