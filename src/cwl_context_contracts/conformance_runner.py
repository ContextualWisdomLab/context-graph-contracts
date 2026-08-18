"""Executable semantic conformance evidence for installed CWL contract packages."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .assertion import ContextAssertion
from .conformance import (
    available_conformance_profile_names,
    load_conformance_profile,
)
from .data_management import validate_data_management_assessment_semantics
from .events import CloudEventEnvelope, _validate_and_freeze_json_value
from .temporal import parse_cwl_timestamp


@dataclass(frozen=True, slots=True)
class ConformanceFailure:
    """One semantic conformance vector that did not behave as published."""

    profile_name: str
    case_id: str
    detail: str

    def to_mapping(self) -> dict[str, str]:
        """Return a deterministic JSON-native failure record."""
        return {
            "profile_name": self.profile_name,
            "case_id": self.case_id,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class ConformanceReport:
    """Aggregate result from executing every packaged semantic vector."""

    profile_count: int
    case_count: int
    failures: tuple[ConformanceFailure, ...]

    @property
    def passed(self) -> bool:
        """Return whether every executable packaged vector behaved as published."""
        return not self.failures

    def to_mapping(self) -> dict[str, object]:
        """Return a stable machine-readable report for release evidence."""
        return {
            "status": "pass" if self.passed else "fail",
            "profile_count": self.profile_count,
            "case_count": self.case_count,
            "failures": [failure.to_mapping() for failure in self.failures],
        }


class ConformanceError(RuntimeError):
    """Raised when the installed reference package fails its own conformance data."""


def _unexpected_exception(exc: Exception) -> str:
    """Return a stable exception description without a traceback or environment data."""
    return f"{type(exc).__name__}: {exc}"


def _expected_rejection(
    *,
    profile_name: str,
    case_id: str,
    error_pattern: str | None,
    action: Callable[[], object],
) -> ConformanceFailure | None:
    """Execute a negative vector and report acceptance or wrong-cause rejection."""
    try:
        action()
    except Exception as exc:  # the vector contract is rejection, not one exception type
        if error_pattern is None or error_pattern in str(exc):
            return None
        return ConformanceFailure(
            profile_name,
            case_id,
            f"rejected with unexpected error: {_unexpected_exception(exc)}",
        )
    return ConformanceFailure(
        profile_name,
        case_id,
        "invalid vector was unexpectedly accepted",
    )


def _expected_acceptance(
    *,
    profile_name: str,
    case_id: str,
    action: Callable[[], object],
) -> ConformanceFailure | None:
    """Execute a positive vector and report any fail-closed rejection."""
    try:
        action()
    except Exception as exc:
        return ConformanceFailure(
            profile_name,
            case_id,
            f"valid vector was unexpectedly rejected: {_unexpected_exception(exc)}",
        )
    return None


def _run_timestamp_profile(
    profile_name: str,
    profile: dict[str, Any],
) -> tuple[int, tuple[ConformanceFailure, ...]]:
    """Execute the CWL Timestamp Profile v1 vectors."""
    failures: list[ConformanceFailure] = []
    case_count = 0
    for index, value in enumerate(profile["valid_values"]):
        case_count += 1
        failure = _expected_acceptance(
            profile_name=profile_name,
            case_id=f"valid_values[{index}]",
            action=lambda value=value: parse_cwl_timestamp(value),
        )
        if failure is not None:
            failures.append(failure)
    for index, value in enumerate(profile["invalid_values"]):
        case_count += 1
        failure = _expected_rejection(
            profile_name=profile_name,
            case_id=f"invalid_values[{index}]",
            error_pattern=None,
            action=lambda value=value: parse_cwl_timestamp(value),
        )
        if failure is not None:
            failures.append(failure)
    return case_count, tuple(failures)


def _run_assertion_profile(
    profile_name: str,
    profile: dict[str, Any],
) -> tuple[int, tuple[ConformanceFailure, ...]]:
    """Execute provider-neutral Context Assertion semantic rejection vectors."""
    failures: list[ConformanceFailure] = []
    vectors = profile["invalid_vectors"]
    for index, vector in enumerate(vectors):
        case_id = str(vector.get("case_id", f"invalid_vectors[{index}]"))
        failure = _expected_rejection(
            profile_name=profile_name,
            case_id=case_id,
            error_pattern=str(vector["error_pattern"]),
            action=lambda vector=vector: ContextAssertion.from_mapping(vector["value"]),
        )
        if failure is not None:
            failures.append(failure)
    return len(vectors), tuple(failures)


def _run_cloudevent_profile(
    profile_name: str,
    profile: dict[str, Any],
) -> tuple[int, tuple[ConformanceFailure, ...]]:
    """Execute CloudEvent positive round-trips and semantic rejection vectors."""
    failures: list[ConformanceFailure] = []
    case_count = 0
    for index, vector in enumerate(profile["valid_vectors"]):
        case_count += 1
        case_id = str(vector.get("name", f"valid_vectors[{index}]"))

        def round_trip(vector=vector) -> None:
            parsed = CloudEventEnvelope.from_mapping(vector["value"])
            if parsed.to_mapping() != vector["value"]:
                raise ValueError("valid vector did not round-trip exactly")

        failure = _expected_acceptance(
            profile_name=profile_name,
            case_id=case_id,
            action=round_trip,
        )
        if failure is not None:
            failures.append(failure)
    for index, vector in enumerate(profile["invalid_vectors"]):
        case_count += 1
        case_id = str(vector.get("name", f"invalid_vectors[{index}]"))
        failure = _expected_rejection(
            profile_name=profile_name,
            case_id=case_id,
            error_pattern=str(vector["error_pattern"]),
            action=lambda vector=vector: CloudEventEnvelope.from_mapping(
                vector["value"]
            ),
        )
        if failure is not None:
            failures.append(failure)
    return case_count, tuple(failures)


def _run_json_profile(
    profile_name: str,
    profile: dict[str, Any],
) -> tuple[int, tuple[ConformanceFailure, ...]]:
    """Execute RFC 8259 exact-integer interoperability boundary vectors."""
    failures: list[ConformanceFailure] = []
    case_count = 0
    for index, value in enumerate(profile["valid_integer_values"]):
        case_count += 1
        failure = _expected_acceptance(
            profile_name=profile_name,
            case_id=f"valid_integer_values[{index}]",
            action=lambda value=value: _validate_and_freeze_json_value(value),
        )
        if failure is not None:
            failures.append(failure)
    for index, value in enumerate(profile["invalid_integer_values"]):
        case_count += 1
        failure = _expected_rejection(
            profile_name=profile_name,
            case_id=f"invalid_integer_values[{index}]",
            error_pattern="exact interoperable range",
            action=lambda value=value: _validate_and_freeze_json_value(value),
        )
        if failure is not None:
            failures.append(failure)
    return case_count, tuple(failures)


def _run_data_management_assessment_profile(
    profile_name: str,
    profile: dict[str, Any],
) -> tuple[int, tuple[ConformanceFailure, ...]]:
    """Execute provider-neutral data-management assessment semantic vectors."""
    failures: list[ConformanceFailure] = []
    case_count = 0
    for index, vector in enumerate(profile["valid_vectors"]):
        case_count += 1
        case_id = str(vector.get("case_id", f"valid_vectors[{index}]"))
        failure = _expected_acceptance(
            profile_name=profile_name,
            case_id=case_id,
            action=lambda vector=vector: validate_data_management_assessment_semantics(
                vector["value"]
            ),
        )
        if failure is not None:
            failures.append(failure)
    for index, vector in enumerate(profile["invalid_vectors"]):
        case_count += 1
        case_id = str(vector.get("case_id", f"invalid_vectors[{index}]"))
        failure = _expected_rejection(
            profile_name=profile_name,
            case_id=case_id,
            error_pattern=str(vector["error_pattern"]),
            action=lambda vector=vector: validate_data_management_assessment_semantics(
                vector["value"]
            ),
        )
        if failure is not None:
            failures.append(failure)
    return case_count, tuple(failures)


_PROFILE_RUNNERS: dict[
    str,
    Callable[[str, dict[str, Any]], tuple[int, tuple[ConformanceFailure, ...]]],
] = {
    "cwl-timestamp-profile.v1.json": _run_timestamp_profile,
    "context-assertion-semantics.v1.json": _run_assertion_profile,
    "cloudevent-semantics.v1.json": _run_cloudevent_profile,
    "cwl-json-interoperability.v1.json": _run_json_profile,
    "data-management-assessment-semantics.v1.json": (
        _run_data_management_assessment_profile
    ),
}


def run_packaged_conformance() -> ConformanceReport:
    """Execute every installed semantic profile through the reference SDK.

    The runner deliberately fails closed when a packaged profile cannot be read or
    when a newly packaged profile lacks an executable runner. This makes the same
    semantic vectors usable by buyers, package smoke tests, and release evidence.
    """
    profile_names = available_conformance_profile_names()
    failures: list[ConformanceFailure] = []
    case_count = 0
    for profile_name in profile_names:
        try:
            profile = load_conformance_profile(profile_name)
        except Exception as exc:
            failures.append(
                ConformanceFailure(
                    profile_name,
                    "profile_load",
                    _unexpected_exception(exc),
                )
            )
            continue
        profile_runner = _PROFILE_RUNNERS.get(profile_name)
        if profile_runner is None:
            failures.append(
                ConformanceFailure(
                    profile_name,
                    "profile_dispatch",
                    "no executable runner is registered for this packaged profile",
                )
            )
            continue
        try:
            profile_case_count, profile_failures = profile_runner(
                profile_name,
                profile,
            )
        except Exception as exc:
            failures.append(
                ConformanceFailure(
                    profile_name,
                    "profile_execution",
                    _unexpected_exception(exc),
                )
            )
            continue
        case_count += profile_case_count
        failures.extend(profile_failures)
    return ConformanceReport(
        profile_count=len(profile_names),
        case_count=case_count,
        failures=tuple(failures),
    )


def assert_packaged_conformance() -> ConformanceReport:
    """Return the report or raise on the first installed-package conformance drift."""
    report = run_packaged_conformance()
    if report.passed:
        return report
    failure = report.failures[0]
    raise ConformanceError(
        "packaged semantic conformance failed at "
        f"{failure.profile_name}/{failure.case_id}: {failure.detail}"
    )


def main() -> int:
    """Print the conformance report as JSON and return a shell-compatible status."""
    report = run_packaged_conformance()
    print(json.dumps(report.to_mapping(), sort_keys=True))
    return 0 if report.passed else 1
