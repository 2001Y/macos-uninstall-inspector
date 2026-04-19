# Roadmap

## Milestone 0 — Design publication
- publish architecture, pipeline, strategies, confidence model
- define JSON schema for findings
- define sample outputs
- add validation tests

## Milestone 1 — Read-only inspector MVP
- CLI: inspect one app path
- collect identity metadata
- resolve Homebrew/pkg/MAS/Setapp/vendor provenance
- enumerate bundle helpers, containers, launchd assets, user-state paths
- emit JSON report matching schema

## Milestone 2 — Confidence scoring
- weight evidence
- classify app-owned vs vendor-shared vs heuristic-only
- expose safe/balanced/aggressive filtering

## Milestone 3 — Review UX
- human-readable grouped summary
- reasons per candidate
- warnings for vendor-managed suites

## Milestone 4 — Controlled deletion engine
- explicit dry-run by default
- delete only reviewed candidates
- system asset ordering / process shutdown / receipt handling

## Milestone 5 — Vendor adapters
- Adobe adapter
- Setapp adapter
- future adapters for complex suites

## Test strategy
- unit tests for identity normalization
- fixture-based tests for report schema
- golden JSON outputs for representative app classes
- resolver-specific tests for Homebrew/pkg/MAS/Setapp/Adobe paths
- regression tests for false-positive patterns discovered during live use
