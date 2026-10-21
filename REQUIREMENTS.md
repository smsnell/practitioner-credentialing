# Practitioner Credentialing

## Goal

Build a reusable **Agent Skill** for Larkhollow Community Hospital's Medical Staff Office that processes initial-appointment applications from intake through recorded appointment and authorized activation of clinical privileges. The hospital and records are fictional.

The Skill must operate on real supplied batches and retained state—not merely propose a routing plan, run isolated checks, or produce a final report.

**Starting references:** [starter repository](https://github.com/GitRollTraining/practitioner-credentialing) · [snapshot schema](https://github.com/GitRollTraining/practitioner-credentialing/blob/main/snapshot.schema.json)

## Required behavior

- Consume **one closed export batch per run**, together with state retained from the previous run. Process the three supplied batches in order; batch 3 must resume from batch 2 rather than restart.
- Use each batch's **export date** as the clock for all calculations from that batch, never the execution date.
- For every application in the batch's caseload, assemble the file, apply the office's source-verification rules, track each element's state and outstanding work, and generate an **owned human action queue**.
- Determine packet presentability under the office's rules and bind readiness to the **specific application revision** assessed.
- Consume supplied committee and Governing Body decisions. Check each decision's admissibility and claimed authority against the office's registries, not just the decision record's own claims.
- Record appointment outcomes. Activate **only the privileges actually approved**, no earlier than the effective date permitted by the admissible approval.
- Retain state and history across batches, including refused decision records and unresolved work.

Handle the non-happy paths required by the assignment: missing intake items, unacceptable verification replies, nonresponsive sources, applicant/source discrepancies, evidence becoming stale while waiting, later application revisions, inadmissible decisions, and files that end without appointment.

### Human decisions the Skill must not make

The Skill may prepare evidence, request an owned decision, and record a returned disposition, but must **not** independently decide:

1. Whether a gap explanation is satisfactory.
2. Whether a finding is disqualifying.
3. Whether to discontinue an application on eligibility grounds.
4. Whether to recommend appointment or which privileges to recommend.
5. Whether to grant, modify, defer, or deny an appointment/privileges decision.

Outstanding human decisions belong in the action queue with their owner, not in computed approval fields.

### Rule authority

Apply the **office's** rules as supported by its supplied documents and recorded stakeholder answers. Distinguish published-manual rules, office-authored rules (including departures from the manual), and judgments reserved to people. Do not invent thresholds, time windows, acceptable sources, or missing decisions. Flag missing or contradictory rules for clarification.

## Run outcomes

These describe processing results, **not** business approval:

- **Supported:** All three supplied batches consumed, a sealed snapshot for each, and all required files present and consistent.
- **Partial:** A batch was consumed, but some applications or records remain unsettled. Preserve them in the snapshot with outstanding work and owner; log the affected scope and reason.
- **Blocked:** A batch could not be consumed. Log the attempt, error, and affected scope; do not claim an uncomputed snapshot. Preserve the last sealed snapshot while reporting the failed run as blocked.
- **Deferred:** A business hold awaiting a person or body, not a run failure. Preserve the file's status, owner, and awaited event in the snapshot/action queue.

A failed later run must not be reported as though the earlier successful run were the later run's result.

## Snapshot contract

Read `snapshot.schema.json` for **all fields, types, and enumerations**. Do not invent a substitute schema. Snapshots are UTF-8 JSON; dates are `YYYY-MM-DD`; date ranges are inclusive. Preserve unknowns only as allowed by the schema—unknown does not mean zero, false, or no.

Each batch snapshot must cover every application in that batch's caseload, including revision, status, per-element states, packet readiness, decision/admission history and refusal reasons, activation, monitored conditions, and the action queue, as defined by the schema.

The following rules also apply:

1. `as_of` equals the batch's export date.
2. The first snapshot has `predecessor: null`. Each later snapshot references the retained prior snapshot's **path and SHA-256**. A snapshot never hashes itself.
3. `produced` lists every file written or refreshed by the run; `rules_file` resolves to the rule register.
4. Every `decision_id` comes from the office's actual decision record. A refused record and its reason remain in all later snapshots.
5. If `approval_decision_id` is set, it names a decision in that same application's `decisions` with `admitted: true`.
6. `deliverables/snapshots/batch-0N.json` always contains batch N's **current occurrence**. A snapshot becomes **sealed on repository commit**; an uncommitted working snapshot may be regenerated. Never rewrite a sealed occurrence. If a correction changes one, regenerate it and all downstream snapshots under their standard paths in a new commit, preserve each superseded occurrence unchanged under a distinct filename, assign new `snapshot_id` values, and document the supersession in the run log. An unchanged rerun keeps the existing sealed snapshot.

## Required technical deliverables

| Path | Required contents |
| --- | --- |
| `SKILL.md` and supporting files | Reusable Skill metadata, inputs, one-batch invocation, authority limits, outputs, failure/rerun behavior, and references to implementation and source rules. Do not hardcode case-specific answers. |
| `README.md` | Setup and dependencies; exact commands to run and resume batches; meaning of Supported, Partial, Blocked, and Deferred outputs; verification and handoff instructions. |
| `deliverables/snapshots/batch-01.json` through `batch-03.json` | Schema-conforming, history-linked snapshots for the three batches. |
| `deliverables/rules.md` | Every applied rule and its precise source (office document/section or stakeholder-interview turn); distinguish published and office-authored rules. |
| `deliverables/verification.md` | Checks of actual outputs against source records and applicable rules, including files checked, findings and corrections. Independently recompute **at least one quantity** using something other than the Skill's own code, and describe the method. |
| `deliverables/run-log.md` | One entry per run: command, batch, execution time, inputs, written/refreshed files, and failures with their affected scope. |
