# Practitioner credentialing — operational tracker

Updated: 2026-10-21. Current operational status only; business clock remains the batch export date.
[Unchanged pre-compaction archive](PROJECT-TRACKER-2026-10-21-G1-ARCHIVE.md) retains prior decisions, source references, metrics and review history.
Archive SHA-256: `b6bfb6a5cb05a0dfb4e33a0af9a35b4fe045207ff922c408ab1306cbee5222c6`.
Historical “Partial without snapshot” reports and earlier test counts are superseded, not current acceptance evidence.

## Gate, authorization and acceptance

- **Gate:** G1 checks complete; conditional owner acceptance applies. Seal/push G1 before G2 continuation.
- **Acceptance:** G1 accepted with the documented Q07 exception; full regression suite **140 passed**, existing G1 criteria pass.
- **Current authorization:** local G1 sealing commit/push, metrics update, then G2 sequential continuation through checked/sealed Batch 2 and fresh-process Batch 3.
- **Stop:** G2 review before Batch-3 sealing, G3 or final handoff. Schema/original evidence and architecture remain unchanged.
- Architecture, scope and acceptance gates remain in [IMPLEMENTATION-PLAN.md](IMPLEMENTATION-PLAN.md#2-preconditions-and-proposed-gates).
- Deliverable/outcome authority: [REQUIREMENTS.md](REQUIREMENTS.md); status meanings: [snapshot.schema.json](snapshot.schema.json).
- Rules and sources: [applied-rule register](deliverables/rules.md). Model/effort and bounded delegation: [ORCHESTRATION.md](ORCHESTRATION.md).

## Q07 contract exception

**Owner: project/contract owner.** Q07 remains distinct from practitioner evidence and decisions.
The [single decision record and remaining assessment risk](deliverables/rules.md#q07-owner-approved-semantic-exception) govern the current candidate.
The mapping blocker is addressed by owner authorization; original schema-description compliance and stakeholder reconciliation are **not** established.
Structural/behavior checks and exception acceptance are reported separately in [current verification](deliverables/verification.md#owner-exception-focused-verification).
[Prior source comparison](deliverables/g1-review-response.md#new-clarification-and-q07) and [historical incompatibility proof](deliverables/g1-q07.md) remain preserved.

## Practitioner casework — separate from Q07

**Operational owner: MSP (Renata Kowalczyk)**; applicant supplies corrections/documents, Clinical Director retains reserved judgments.
These are preserved evidence deficits or conflicts, not proof of missing qualifications and not permission to resolve human decisions.
Later-batch items below were identified during planning; they are not G2 processing results and were not imported into batch-1 outputs.

| Scope / case | Outstanding work and owner |
| --- | --- |
| Batch-wide evidence | MSP obtains application signature/date evidence, actual CV contents for reconciliation, required accreditation and direct peer-return provenance. Existing receipt/degree/training/eligibility facts remain retained; absence from the export is not proof of absence in the office. |
| APP-2026-019 | Applicant owes release/CV under the existing February 18 notice, due **March 20**. MSP's new signature-evidence/referee-name requests remain pending with null due dates. Verification outreach remains held for release. |
| Q17 / APP-2026-036 | MSP/applicant reconcile revision prose naming 2019–2025 against changed ENT-3602 (2012–2019); retain VR-3604 on its entry and unchanged ENT-3603. |
| Q17 / APP-2026-034 | Applicant/MSP resolve Ingrid Solheim versus Ingrid Lindholm correspondence identity; no clarification or dispatch is inferred. |
| Q17 / APP-2026-017 | MSP obtains the specifically referenced **February 24** explanation; February 13 cannot substitute. CD disposition must match its evidence. |
| Q17 / APP-2026-018 | Applicant/MSP reconcile Harrowgate versus Silverbeck. Preserve the actual March 6 return and April 5 deadline. |
| APP-2026-015 | Applicant/MSP obtain the numbered correction revision; the PPQ-1 letter/CD disposition do not replace it. Preserve licence finding and discrepancy. |
| GBD-2026-038 / 035 | MSP retains the missing valid same-revision Executive recommendations; unauthorized MEC approval or a revision-1 recommendation cannot satisfy the dependency. No approval inferred. |
| GBD-2026-039 / Q16 | MSP retains explicit November 30 and June 30 conditions separately from the general December 31 licence-expiry obligation, with provenance. |

Case evidence/verification targets: [implementation plan](IMPLEMENTATION-PLAN.md#5-focused-verification-matrix); detailed source associations and transcript spelling/ID differences: [archived issue register](PROJECT-TRACKER-2026-10-21-G1-ARCHIVE.md#5-g0-reassessment-and-remaining-issues).
Referee addresses remain explicitly not assessable. No attestation or broad “clean file” claim supplies missing underlying facts.

## Other bounded residuals and handoff obligations

- **Policy/contract owner, if encountered:** Q04 partial-duration arithmetic; Q05 backdate/version boundaries; Q06 receipt/completion timing; Q07 late-cure reopening; Q09 post-activation consequences; Q10 leap-day/designation boundaries.
- Preserve affected holds rather than inventing policy, dates or automatic suspension. These are not new investigation tasks or blanket case blockers.
- **Owner/facilitator — Q13:** verify actual session-capture coverage at the existing handoff gate; a self-written log is not capture evidence.
- Detailed limits and source-document defects remain in [archived residuals](PROJECT-TRACKER-2026-10-21-G1-ARCHIVE.md#bounded-residuals-and-execution-prerequisites); gate obligations remain in the plan.

## Latest verification and retained output

- **Latest verification: full suite 140 passing tests**, run once after refusal-action correction; [existing G1 criteria pass](deliverables/verification.md#final-g1-acceptance-check--2026-10-21).
- Real batch 1: **40 applications / 41 revisions**, **39 intake-incomplete / 1 returned-incomplete**; six refused recommendations; **zero ready packets, approvals or activations**.
- CLI outcome: **Partial**, exit **0**, with a complete structurally valid candidate. G1 acceptance follows explicit conditional owner authorization; original-description compliance is not claimed.
- Final correction adds exactly six MSP refusal actions with decision IDs/reasons and null deadlines; all prior fields/actions, history and packets are unchanged.
- All 46 protected source/input/interview/schema/instruction/archive hashes match; prior run-log bytes are retained. Schema and source evidence remain unchanged.
- Focused checks distinguish pending dispatch, running clocks, expiry and fulfilled older requests; synthetic fixtures add no actual events. [Verification details](deliverables/verification.md#owner-exception-focused-verification).
- [Skill scan](deliverables/skill-scan.md#q07-owner-exception-follow-up-scan): exit 1; same documented argv false positive and license-information item. No clean-scan claim.

Artifacts: [candidate snapshot](deliverables/snapshots/batch-01.json), [results](deliverables/working/batch-01/results.json), [history](deliverables/working/batch-01/history.json), [packets](deliverables/working/batch-01/packets.json), [run metadata](deliverables/working/batch-01/run.json), [append-only run log](deliverables/run-log.md).
Sources: [batch manifest](inputs/batch-01/manifest.json), [standing-source manifest](sources/manifest.json), [original interviews](interviews/), [independent review](deliverables/g1-independent-review.md).

## Scoped metrics

| Measure | Last recorded scope / value |
| --- | --- |
| Prior recorded turns | **87m38s** through the completed tracker cleanup, including its **5m02s**. |
| Q07 exception implementation | **7m26s** this turn (07:02:11–07:09:37 UTC); **95m04s** cumulative recorded turns. |
| Planning push `a710f80` | **6,728,488 tokens** including cache reads; checkpoint `01M5E6YXSCCDRZJQYW467ZWY24`, one session / 63 calls. |
| Metrics push `f2b6bff` | **778,856 tokens** including cache reads; checkpoint `01M5E71WN6VY88GQ128ZXTJ854`, 9 calls; reported separately. |
| Current token/cost availability | No new push checkpoint; per-agent token totals, aggregate model-active time and cost unavailable. Do not sum checkpoint counts without comparable scopes. |
| Estimates | Owner's 3–4 hours / 50M tokens are estimates, not targets. Last remaining estimate: **3–5 active hours**, provisional pending next-gate authorization; later-batch integration remains unexercised. |

Time is measured active-turn wall time including tool waits; inter-turn waiting is excluded and parallel worker time is not added twice.
Token totals include cached reads, are not cost estimates or a guaranteed whole-project total, and are not E-5/G1-only increments.
Breakdowns, capture association and stale-counter caveats: [archived metrics](PROJECT-TRACKER-2026-10-21-G1-ARCHIVE.md#8-progress-estimates-and-metrics).
Report time after each turn and reliable token counters after an authorized push; do not generate a push to obtain metrics.

## Next action and supporting records

1. **Agent:** seal/push accepted G1 and record reliable checkpoint metrics, then execute the existing G2 plan sequentially.
2. **Owner:** review G2 three-batch results at its existing boundary; practitioner casework remains outstanding.
3. **Future allocation only:** [archived G2–G3 proposal](PROJECT-TRACKER-2026-10-21-G1-ARCHIVE.md#proposed-g2g3-allocation--not-started) follows ORCHESTRATION.md and unchanged gates; G2 implementation follows G1 sealing.

[Prior review response](deliverables/g1-review-response.md) retains the correction narrative and parser limits; [applied rules](deliverables/rules.md) own rule/source detail; [plan](IMPLEMENTATION-PLAN.md) owns architecture, scope and gates; [README](README.md) owns run instructions.
The archive preserves historical decisions, source references and superseded results unchanged. Original interviews, source captures, diagnostic artifacts and run logs remain preserved.

## Bounded delegation update

Lead retained policy mapping, integration and decision documentation; reused **Sol 6.1 High** for the isolated Q07/IO regression update (two files, 24 passing checks). High effort matched the structural-versus-semantic contract distinction. No overlapping edits or integration issues; no new framework or discovery. Per-worker tokens/cost are unavailable. Existing [G2–G3 allocation](PROJECT-TRACKER-2026-10-21-G1-ARCHIVE.md#proposed-g2g3-allocation--not-started) remains a proposal only.

Final G1 bounded delegation: Sol 6.1 Medium owned only eight refusal-action tests; lead owned the small projection change and the single full-suite/acceptance check. No overlapping edits or integration failure.
