# ADR 0005: Use CloudEvents with provenance references

- **Status:** Accepted
- **Date:** 2026-08-16

## Decision

Cross-service notifications use CloudEvents 1.0.2 structured JSON. Material
assertions reference evidence through a canonical URI and SHA-256 digest.

## Consequence

Transport remains broker-neutral, while authorization and evidence retention
remain the responsibility of each domain service.
