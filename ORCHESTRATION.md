# Orchestration

This file adds model allocation and delegation only. Follow `AGENTS.md`, `REQUIREMENTS.md`, and the existing implementation plan/gates; keep task ownership and progress in `PROJECT-TRACKER.md`.

## Models

- **Astra High:** lead orchestration, architecture, difficult policy/state/decision logic, integration, and final review. High is the ceiling; no Extra High.
- **Sol 6.1:** delegate suitable bounded implementation, tests, documentation, and isolated debugging. The lead selects effort according to complexity and observed results.

## Delegation

- Identify useful Sol tasks within each approved stage, including Gate 1. Delegation can be sequential; parallelize only genuinely independent work.
- Give each task a clear outcome, relevant context, file ownership/interfaces, and targeted acceptance check. Require changed files, check results, and unresolved issues in the return.
- Keep shared policy/state integration under one lead, not necessarily one implementer. Avoid overlapping edits; use separate worktrees when useful. The lead inspects changes and checks integration.
- No fixed worker count, extra orchestration framework, or duplicate review pipeline.

## Review cadence

**Intermediate gates:** focused tests, integration checks, and owner acceptance under the existing plan—not a comprehensive Astra High review.

**Project completion:** one integrated Astra High review after implementation and checks. Fix material findings and verify the affected behavior; repeat the broad review only if substantial changes invalidate it.
