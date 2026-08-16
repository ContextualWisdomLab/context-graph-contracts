# ADR 0004: Separate valid time from system time

- **Status:** Accepted
- **Date:** 2026-08-16

## Decision

Interchange contracts carry real-world validity and system-recording intervals.
Open intervals omit the end value instead of using sentinel dates.

## Consequence

Consumers can reproduce historical knowledge cutoffs and avoid future-information
leakage in impact or audit analysis.
