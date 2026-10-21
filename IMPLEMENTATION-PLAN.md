# Practitioner credentialing — bounded implementation plan

Status: **G1 accepted with the documented Q07 exception after the final refusal-action correction, 140 passing regression tests and existing G1 checks. Owner authorizes G1 local sealing/push, then G2 under the unchanged sequence and review boundary.**

E-5 update: preserve the local architecture, 40-file cumulative caseload, 39 CSVs, 82 indexed documents and bounded G1–G3 gates. Missing intake evidence holds the file with a pending MSP dispatch action; the clock starts only on actual dispatch. E-5 permits a consistent refusal-check order and clarifies handling of Q17 cases. Missing evidence and source conflicts remain owned work rather than blanket development blockers. Schema confirmation and its remaining pre-dispatch limitation are recorded below.

Current status, authorization and owners are in [PROJECT-TRACKER.md](PROJECT-TRACKER.md). Applied rules and source references are in [deliverables/rules.md](deliverables/rules.md); detailed historical issue decisions remain in the [unchanged tracker archive](PROJECT-TRACKER-2026-10-21-G1-ARCHIVE.md#5-g0-reassessment-and-remaining-issues). [REQUIREMENTS.md](REQUIREMENTS.md) owns deliverables; [snapshot.schema.json](snapshot.schema.json) owns snapshot fields/types/enums. This plan does not fill missing business rules with defaults.

## 1. Deliverable and boundaries

Deliver a local, reusable Agent Skill that processes **one supplied closed export per invocation**, plus retained prior state; computes each file's state as of that export; preserves evidence/history; and produces an owned human action queue and snapshot. Run all three supplied batches in order, with batch 3 resumed from batch 2 in a fresh process.

Proposed smallest design: Python standard library for CSV, files, dates and hashing; one JSON Schema validation dependency; one CLI; a small set of functions for intake, evidence, dates, readiness and decisions. Parse the supplied UTF-8 CSVs and labelled Markdown documents; retain cited prose evidence for dispositions, conditions, corrections and exceptions. Avoid generic workflow engines and case-ID branches. Keep office registry data and source-backed rules separate from executable logic. No UI, database, hosted service, scheduled polling or automatic correspondence is proposed. The user explicitly preserves this architecture in the E-4 review; Q12 is closed for this bounded plan.

The tool may identify required communications and record supplied communications. **A queued action is not a sent request, a returned disposition or an approval.** The 30-day deadline is recorded request date +30 days, inclusive, with no restart for partial replies/revisions. Only peer requests use the specified 21-day cadence. All five reserved judgments stay with their named owners. I3's routine-reminder policy does not authorize this agent to send messages.

## 2. Preconditions and proposed gates

These are proposed acceptance boundaries. At each owner gate, provide the named evidence and stop; proceed only under the approval recorded for that gate. Do not consume a later batch to work around a failed earlier gate.

| Gate | Evidence and acceptance criteria | Stop / decision |
| --- | --- | --- |
| G0 — discovery and scope | E-5 rules incorporated; consistent refusal order selected; original schema structurally checked and unchanged. Outstanding evidence, Q17 cases and the pre-dispatch schema limitation are explicitly bounded. Architecture preserved. | **Planning complete at owner direction.** Commit/push the planning checkpoint and record available metrics. Stop before G1; no implementation or relaxation of later acceptance gates. |
| G1 — smallest complete batch | One real batch-1 invocation produces a complete candidate snapshot, retained history, owned actions and run log; all caseload entries covered; schema and targeted source checks pass; at least one independent calculation recorded; no invented decisions or executed outreach. Show unsettled cases and reasons. | Owner reviews actual candidate output before first sealing commit and before processing batch 2. |
| G2 — continuation and history | After G1 approval/sealing, process batch 2, check/seal its occurrence, then start a fresh process on batch 3 with batch-2 snapshot/state. Verify predecessor hashes, carried history, changed revisions, stale evidence and authorized activation. Any substantive discrepancy stops progression before the next seal/run. | Owner reviews three-batch results and verification report before final acceptance/handoff. Batch-2 seal authority should be agreed at G1; no implicit approval assumed. |
| G3 — reusable handoff | Required files exist and agree; run/resume/failure/rerun commands documented and exercised; Skill package checked; actual capture evidence checked by owner/facilitator; remaining work clearly owned. | Stop at approved scope. Commit/push or submission only within owner authorization; report available metrics after push. |

An unknown rule affecting an isolated case can become Partial only when the contract can truthfully represent that case and owner/action. If missing data prevents identifying the caseload, revision, export date, or other required non-null facts, report Blocked and preserve the last sealed snapshot. Do not fabricate required values to satisfy validation. Business deferrals and pending human judgments can be correct computed results.

### Current G0 disposition and schema confirmation

G0 planning is complete under the owner's instruction to preserve unresolved cases instead of delaying development. Missing signature/date, CV reconciliation, accreditation and direct-reference provenance remain outstanding. The two identified GB records still lack qualifying recommendation evidence, APP-2026-015 lacks the required numbered correction revision, and Q17 retains source discrepancies plus the specifically missing APP-2026-017 explanation dated 2026-02-24. E-5 supplies handling rules, not replacement evidence.

**Schema checked:** `snapshot.schema.json` is valid Draft 2020-12 under `Draft202012Validator.check_schema`; schema version `credentialing-snapshot/1`, 13 application-status values, seven element states and the six required element keys are preserved. SHA-256: `df371cfd4638194348be79352a0683d9d4dc40bb4f95d87f6028a7b889274318`. No schema edits or fabricated sample snapshots were made. Structural validity does not prove that every business state has a truthful representation.

**G0 Q07 disposition (historical; current projection follows the [owner exception](deliverables/rules.md#q07-owner-approved-semantic-exception)):** before dispatch, hold the file, queue MSP's written request, use null for an unrecorded due date and leave the applicant clock unstarted. **Compatibility limitation retained:** S's `intake-incomplete` description requires an already-sent request and running clock; E-5 supplies no new status. Preserve this state in working history/actions without inventing dispatch, completeness or an enum. Development of known logic can proceed when authorized, but an affected unrepresentable file still prevents claiming a complete semantically conforming G1 snapshot. Report that output limitation at the unchanged G1 gate; do not omit the case or label a partial/invalid snapshot accepted.

**Q03-order is closed:** E-5 permits engineering to choose a consistent order, retaining all failures. Keep P's five original checks in order, then check the criteria version in force at the decision date, separately valid same-revision Executive Committee recommendation for GB approval, and duplicate/supersession. S stores the first failure; retained history/logs store all failures. This is the chosen implementation order, not a claim of office-prescribed priority.

Q17 reconciliation/missing-document actions are owned casework, not unresolved policy. Preserve source facts and interview/source identifier or spelling differences. Q13 actual capture/environment remains an execution prerequisite; planning commit/push is authorized, and capture evidence must be distinguished from the mere presence of hooks. The latest owner instruction authorizes G1 implementation and focused verification; commit/seal, push and batch 2 remain outside this turn.

## 3. Implementation sequence after G0

Original G0 active-work estimate: **240–360 minutes (4–6 hours)**. After G1 work, provisional remaining estimate is **3–5 active hours after Q07 output disposition and next gate authorization**; actual later-batch integration is still unexercised. Input access is resolved; the larger range accounts for 40 files, 82 narrative documents, historical reconstruction and concrete evidence conflicts. It excludes waiting for missing evidence and is not a deadline or spend target. Re-estimate at G1; each stage ends with a targeted check.

| Stage | Smallest change and intended output | Targeted check | Estimate |
| --- | --- | --- | --- |
| 1. Freeze input contract and rules | Use completed inventory; capture original input bytes/hashes, map standing-source filenames and record E-3/E-4/E-5 rules and owner dispositions. Apply confirmed missing-evidence handling and Markdown extraction; build applied-rule register. | 13 CSVs per batch, 82 indexed paths, confirmed join keys and 40-file caseload; no silent evidence assumptions. | 25–40 min |
| 2. One-batch state transition | Implement ingestion, retained history, intake, source checks, gaps, support, peer eligibility/currency and actions. Parse relevant prose with source references; continue unaffected entries. | Real B1 cases plus focused date, provenance, incomplete-intake, discrepancy and revision boundaries. | 80–110 min |
| 3. Readiness and decisions | Implement historical readiness, roster validation, same-revision recommendation/version checks and the reviewed refusal order, supersession, activation/cycle dates and conditions. | No retroactive readiness; persistent findings; exact grants; missing recommendation cannot be invented; terminal results. | 50–80 min |
| 4. Snapshot lifecycle and continuation | Validate/stage snapshots, state and logs; resume sequentially; preserve sealed occurrences and unchanged reruns; record failures. | G1/G2: 40 files in each snapshot, predecessor/history checks, fresh-process B3 resume and accurate failure reporting. | 50–75 min |
| 5. Skill and handoff | Write Skill/README and exact commands. Complete verification, independent calculation and package checks. | G3 artifact inventory, reproducible commands, source consistency, no case-specific answer branches or authority overreach. | 35–55 min |

Stages 2–4 are developed around a complete batch-1 result before G1. Later batch execution in stage 4 waits for G1 approval. G0 discovery created no implementation artifacts. Authorized G1 provides the local processor, first-batch candidate and focused checks under the [owner exception](deliverables/rules.md#q07-owner-approved-semantic-exception); G1 acceptance and sealing remain pending.

## 4. Proposed retained state and processing order

Use a simple JSON working-state artifact alongside each snapshot, plus source records or immutable references. The contract snapshot alone cannot retain the history needed for correct continuation. Exact internal paths/fields remain a small implementation choice, not additions to S.

Confirmed input contract: B1 export 2026-03-16 contains 41 application revisions for 40 files (including two revisions of APP-2026-025); B2 export 2026-04-20 adds four revisions; B3 export 2026-05-18 adds one. Later batches append observations and never delete terminal files. Applicant facts join on application/revision; WA rows join on the four name/birth-year fields. Preserve earlier lookup observations when later selective exports omit them. Header-only CSVs are valid. Apply only explicitly defined blank meanings, including non-expiring certification, without treating `Not certified` as Active; board eligibility can be stated in notes (CR-01000).

The export provides no precomputed queue, status or packet. Generate a revision-bound packet manifest/evidence summary as well as readiness, retaining findings and source links; do not claim physical presentation or a committee decision occurred merely because a packet was generated. Referee addresses must be recorded as not assessable, not failed. Other absent signature/CV/accreditation/provenance evidence remains outstanding under I4 21:33; neither a row nor an office attestation substitutes for official evidence. CV presence is not reconciliation. No affected readiness or verification is inferred.

Retain at least:

- Batch identity/export date, input filenames and content hashes, source/rule versions, prior snapshot identity/hash and linkage to corresponding working state.
- Every application revision, first-received anchor and the current revision; entry identity/content and evidence provenance, including sender role, route, signature/completion/receipt dates where supplied.
- Attempt logs and actual written-request dates; gap intervals/explanations; discrepancies and resolutions; required human dispositions; queued versus completed actions.
- Readiness occurrences by revision, event date and supporting evidence; invalidation reasons; criteria version and requested/supported/unsupported groups.
- Every actual decision ID in received order, claimed authority, admission result/first refusal condition, supersession links, outcomes, activation, monitored conditions and closure events.

Per invocation:

1. Validate input manifest/export date and required source availability. Verify predecessor snapshot hash and matching retained state. Reject a missing/mismatched predecessor; batch 3 cannot silently restart.
2. Append this batch's rows/documents to retained state. Revision-scoped tables restate that revision's facts; do not merge old declarations into the latest revision by ID alone. Deduplicate unchanged stable observations without discarding history; retain cumulative caseload; never use future-batch evidence.
3. Use supplied event dates, preserving correspondence index order for received records without inventing time-of-day precedence. Reassess revisions, dispositions and affected entries. Require necessary readiness evidence strictly before decision date, except the explicit same-day board-lookup rule. Do not backdate readiness to the last reply when a required revision/disposition arrived later.
4. Apply completeness, reconciliation, provenance and element checks. Missing required evidence stays outstanding. Preserve a finding and unresolved discrepancy separately internally; project the mixed entry as `outstanding` with both facts retained, and prevent readiness until required work is resolved. Every declared-information correction requires a new numbered revision; correspondence/disposition alone cannot overwrite declarations or fabricate that revision. Compute owned work without inventing sent requests, clinical judgments, reply dates or acceptable sources.
5. Reconstruct readiness for each relevant historical revision/date. Validate decisions against registry, packet and criteria version. GB approval also requires a separately valid Executive Committee recommendation for that same revision; validate its authority/readiness/outcome independently. Reject an unauthorized committee approval without relabelling it; GB narrative cannot replace a recommendation. Preserve refused records, explicit supersession and the first failed condition using the fixed order in B45; retain every failure internally and in logs.
6. Derive export-date status, readiness, approval pointer, activation, conditions and actions. Apply S's status precedence while retaining reasons and detailed history. Preserve pre-dispatch holds/pending actions with no invented clock (B44). If a required status cannot be represented truthfully under unchanged S, preserve the computed work and report the output limitation accurately; do not publish an incomplete candidate as a complete snapshot or fabricate a status/event. Keep consumed-but-unsettled work distinct from an unconsumable batch.
7. Validate the candidate against S and semantic invariants; build `consumed`, `produced`, rules reference and the run entry. Write candidate outputs to staging so failures cannot overwrite the prior sealed result.
8. Promote a valid candidate as an unsealed working occurrence. Commit/seal only at authorized gates. A batch with a valid snapshot preserving unsettled work is Partial. Failure to produce a truthful conforming snapshot is Blocked, even when inputs were parsed and diagnostic work retained; log that distinction without claiming a snapshot.

No new public snapshot fields for run outcome, timestamps or detailed evidence: S disallows them. Put operational results in the run log and retained artifacts, and list those artifacts in `produced` when written/refreshed.

## 5. Focused verification matrix

Use actual supplied records for acceptance. Synthetic boundary fixtures may supplement them, clearly labelled, and may not substitute for consuming the three exports. Where source policy is unanswered, record the missing expected result and resolve it before asserting a pass.

| Area | Cases to check | Pass evidence |
| --- | --- | --- |
| Intake and authority | All nine checks; unsigned release; missing written request; response on day 30 versus after; partial response/new revision; withdrawal; authorized versus unauthorized discontinuation. | Correct status/action owner; no verification request without release; no fictitious correspondence or clinical decision. |
| Source acceptance | Direct accepted primary/equivalent; applicant-routed genuine-looking reply; unlisted source; closed school/employer; nonresponsive existing source. | Rejected material retained; outstanding work persists; only documented element-specific impossibility enables secondary route. |
| Gaps and history | 29/30-day and 179/180-day intervals; inclusive endpoints; overlapping and open entries; explanation partially covering gap; date and non-date revision changes; five-year overlap boundary. | Exact interval evidence, proper incomplete/routing result, unaffected entries retained, first-receipt anchor stable. |
| Peers | Zero/one/two valid peers; discipline/relationship/direct-work exclusions; second signature anniversary; +21/+42/+64 follow-up; extra open request with two valid peers; evidence stales while awaiting review. | Correct count/currency/actions; no silence counted; surplus request does not block met requirement and closes only on documented presentation. |
| Privileges and findings | Inactive certification; valid/expired board eligibility by allowed group; missing training; CARD fellowship plus residency; some versus no supported groups; later support removes eligibility question; disposition-resolved licensure finding. | Unsupported subset exact; competency not auto-adjudicated; finding persists; required holds remain or end only under policy. |
| Readiness and decisions | Reply on first-received day; reply on decision day; board lookup on decision day; revision/disposition after last reply; authority term boundary; committee approval claim; missing reason; wrong applicant/revision; duplicate GB record; explicit supersession. | Packet evidence predates admitted decision; ordered first refusal reason; no retroactive readiness; proper disposition/recommendation/approval distinctions. |
| Activation and monitoring | Requested versus granted subset; future effective date; absent effective date; backdate policy once clarified; one-year cycle; expiring Washington licence; conditional approval; unmet due condition; named satisfaction. | Exact approved codes and dates, no early activation, monitored due dates, owned findings, no invented suspension policy. |
| Batch continuity | Complete caseload coverage; accumulated refusals and attempts; revision carryover; batch-3 fresh-process resume from batch 2; no later evidence imported early. | Snapshot and state references agree; correct export clock and SHA-256; full history retained. |
| Failure/rerun | Malformed input, unknown required facts, mismatched predecessor, unchanged rerun, correction after sealing. | Last sealed bytes preserved; attempt accurately logged; no fake later snapshot; correction archives original bytes and regenerates entire affected downstream chain with new IDs. |

E-3/E-4/E-5 supply these concrete verification targets; expected results follow confirmed rules and explicitly outstanding evidence:

- **Input/evidence contract:** 13 CSVs per batch; totals 1,631/214/100 data rows; all 82 indexed documents; 40 applications in every snapshot. Referee addresses are explicitly not assessable. Missing application signature/CV reconciliation/accreditation/direct-return evidence stays outstanding (B40); it must not be counted as a verified check, even if no affected file can become ready. Before dispatch, expect a held file, MSP dispatch action, null unrecorded due date and no applicant clock; report the remaining schema limitation rather than inventing a sent request (Q07/B44).
- **Historical revision readiness:** APP-2026-025's original 2024 receipt and two B1 revisions; APP-2026-036's unchanged dates but changed employer/contact, late VR-3604 and decisions against different revisions. Preserve Q17's conflicting narrative rather than silently correcting it.
- **Recommendation dependency:** GBD-2026-038 after unauthorized MEC-2026-036; GBD-2026-035 on revision 2 with only a revision-1 MEC record. Under I4/B41 neither has the required valid same-revision recommendation on supplied evidence. Do not admit either on a GB narrative or relabel the unauthorized MEC outcome. Preserve other admission failures; evaluate the first reason under the selected B45 order without assuming the recommendation failure is first.
- **Written correction and mixed states:** APP-2026-015's B3 PPQ-1 correction letter and CD disposition do not replace the missing numbered revision. Preserve revision 1's declaration, correction evidence, outstanding revision work, restricted-licence finding and discrepancy; no fabricated revision or clean/ready result. Mixed unresolved entry remains `outstanding`, with both facts retained (I4/B42–B43).
- **Q17 retained casework:** preserve APP-2026-036's changed-entry dates and conflicting revision prose; APP-2026-034's correspondence-name discrepancy; APP-2026-018's employer discrepancy; and the specifically missing APP-2026-017 explanation dated 2026-02-24. The February 13 letter cannot silently substitute. No interview promise counts as dispatched correspondence; no source correction was supplied. Preserve the interview's identifier/spelling differences in provenance.
- **Conditions and expiry:** preserve GBD-2026-039's explicit 2026-11-30 and 2026-06-30 due dates alongside the applicable general licence expiry rule (Q16). Test header-only tables and CR-01000's board-eligibility note with blank expiry.
- **Invalid versus unresolved evidence:** keep refused records and contradictions even when later work proceeds. Known duplicate/supersession examples are GBD-2026-036/037 for APP-2026-037 and GBD-2026-034/035 for APP-2026-036. No final admission outcomes have been computed in this review.

**Independent recomputation:** choose a real application's uncovered interval, manually count inclusive days using a calendar or a separate spreadsheet formula `end - start + 1`, and compare the gap threshold/routing and snapshot/retained evidence. Alternatively independently compute a real appointment cycle or deadline once boundary rules are settled. Record exact input file/record, dates, method, expected value, output path, result and any correction in `deliverables/verification.md`. Do not call or copy the Skill's date helper for this check.

Schema validation must enable date-format checks and be supplemented by semantic checks: caseload uniqueness/completeness, real decision IDs, admitted approval pointer, ordered refusals, exact privilege subset, temporal readiness, predecessor bytes, required histories, rules/file existence and a complete `produced` list. A schema-valid file alone is not acceptance.

## 6. Sealing, corrections and failure reporting

Before each sealing commit, check the candidate snapshot and working state together and record their actual paths. An uncommitted snapshot may be regenerated. Once committed, its occurrence is immutable.

For a correction to a sealed occurrence: retain its original bytes under a distinct archived filename; do the same for all superseded downstream occurrences; regenerate current standard paths with new snapshot IDs and correct predecessor hashes; document why and which occurrences were superseded; seal as a new commit. Unchanged reruns retain the existing snapshot and log the attempt without falsely claiming a new occurrence. A changed predecessor makes downstream replay necessary.

On a failure, report the attempted batch, command, execution timestamp, input scope, error and files actually written. Keep business unresolved work distinct from an unconsumable batch. Never label the earlier batch's snapshot as the result of a failed later run. Exact run-outcome reporting belongs in README and the run log because S has no run-outcome field.

## 7. Required handoff artifacts

| Artifact | Acceptance |
| --- | --- |
| `SKILL.md` and supporting files | Reusable metadata, one-batch invocation, inputs/outputs, human authority limits, source references, failure/rerun instructions; no case-specific answer tables in code. |
| `README.md` | Actual setup/dependencies, exact run/resume/verify commands, output meanings, retained-state location, correction/sealing behavior and handoff. |
| `deliverables/snapshots/batch-01.json` through `batch-03.json` | One current occurrence for each export; schema-valid and source-checked, sealed at authorized commits, linked by predecessor path/hash. |
| Working state/history, packet manifests and source provenance | Sufficient for a fresh process to resume without losing entries, attempts, revisions, evidence, readiness, decisions or owned work. Packets cite evidence/findings for the assessed revision; generating one does not invent a presentation event. Listed in run outputs as applicable. |
| `deliverables/rules.md` | Every applied rule with exact office section or interview turn, published/office/human classification, clarified ambiguities and version. |
| `deliverables/verification.md` | Actual files/records checked, expected versus observed results, corrections, independent numerical recomputation and remaining limitations. |
| `deliverables/run-log.md` | Every actual run/attempt: command, batch, execution time, consumed/written files, outcome, failures/affected scope and supersessions. |
| Original interviews and real coding-session capture | Preserve interview exports unchanged; owner/facilitator confirms real capture and its association with submitted revision. A self-written log cannot replace capture. |

## 8. Metrics and next decision

Track elapsed active-turn time after each turn in PROJECT-TRACKER.md. Separate stakeholder waiting from active work and keep execution time separate from business export dates. Report reliable token totals after each authorized push if exposed; otherwise state unavailable. The owner's 50M-token estimate is not a consumption goal. Input formats/volume are now known; the revised 4–6-hour range will be checked at G1 against actual work. G1 active implementation time is now tracked separately from discovery. Record the authorized planning push, capture evidence and any available token totals in the tracker; no counter is inferred from file size or estimates.

**Current boundary:** implement and verify the first batch, then stop at G1 for owner review. Preserve all unresolved work and the documented schema limitation. Do not commit, seal, push or process batch 2. Follow ORCHESTRATION.md for bounded Sol 6.1 tasks and lead integration; no later gate is waived.

## 9. G1 review checkpoint

**Historical checkpoints below:** null-status/no-snapshot outcomes describe earlier runs. The current owner exception follow-up at the end of this section and linked verification govern the candidate now awaiting review.

The real first export was consumed with 40 files and 41 revisions preserved, six recommendations refused for missing prior presentability, and no inferred readiness/approval/activation. Eighty-five focused tests pass; independent calendar counts and source/output checks are recorded in [deliverables/verification.md](deliverables/verification.md). All working artifacts remain uncommitted.

Thirty-eight files require the known pre-dispatch state absent from S. They remain in working JSON with explicit null-status limitations and owned actions; no contract snapshot is emitted. G1's complete-candidate criterion is therefore **not yet satisfied**. Owner review is the current stop. Evidence gaps and Q17 remain casework; the architecture and G1–G3 acceptance text are preserved. No batch 2, snapshot sealing or push occurred.

### Focused G1 troubleshooting follow-up

[Findings and corrections](deliverables/g1-troubleshooting.md) trace APP-2026-001's genuine export omissions and demonstrate Q07 with isolated schema probes. APP-2026-019's existing release/CV requests retain March 20 deadlines; newly pending signature-evidence/referee-name requests have no dispatch or deadline. Incorrect blanket Q04 wording was corrected without clearing accreditation. Sixty-four targeted checks passed at that historical checkpoint; latest verification is below. The proposed schema-description edit was not authorized; current projection follows the later [owner exception](deliverables/rules.md#q07-owner-approved-semantic-exception). Proposed G2–G3 delegation is retained in [archived tracker §11](PROJECT-TRACKER-2026-10-21-G1-ARCHIVE.md#proposed-g2g3-allocation--not-started), under [ORCHESTRATION.md](ORCHESTRATION.md) and future authorization. Stop at G1; no G2 work, commit, sealing or push.

### Independent-review response and new expiry clarification

[Source comparison and implemented corrections](deliverables/g1-review-response.md) supersede the earlier no-snapshot “Partial” terminology. Signature/CV/accreditation/peer provenance checks now clear with qualifying underlying evidence; revision reconciliation no longer imposes a new request-date condition; contact intake is limited to employers/affiliations without mandatory email. Expiry applies only to still-missing items covered by an actual notice. **Historical checkpoint: 129 targeted checks passed; output was diagnostic with snapshot production Blocked.** Current candidate verification is [recorded separately](deliverables/verification.md#owner-exception-focused-verification).

The new stakeholder statement confirms formal incomplete/ineligible treatment follows the thirty-day response period after written request. It does not establish pre-expiry completeness or resolve E-5's pre-dispatch hold, the schema's running-clock `intake-incomplete` meaning, or the procedure's separate gap-return rule. Q07 remains. The prior status-description expansion is an unapproved proposal whose terminology now also needs reconciliation; it is not settled or implemented. No schema or gate change. Stop for G1 review.

## G1 owner exception follow-up — 2026-10-21

The [canonical owner decision and assessment risk](deliverables/rules.md#q07-owner-approved-semantic-exception) supersede the earlier pending mapping authorization. The original schema, evidence, architecture and gate criteria remain unchanged. Review the [candidate and focused checks](deliverables/verification.md#owner-exception-focused-verification) at G1; no G2 or sealing is authorized.

## Current authorization — G1 acceptance and G2

The owner’s conditional acceptance is satisfied by the [final G1 checks](deliverables/verification.md#final-g1-acceptance-check--2026-10-21). Seal/push G1, record available checkpoint metrics, then implement the existing continuation plan. G2 authorization includes checking and locally sealing Batch 2 before a fresh-process Batch 3 resume. Stop with three-batch results for G2 review; no Batch-3 sealing, G3 or final handoff is authorized. Earlier stop instructions above describe their historical turns.
