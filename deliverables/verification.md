# Gate 1 verification

**Current G1 result: accepted under the owner's conditional authorization, including the documented Q07 exception.** The final bounded refusal-action correction passed the full suite and existing G1 criteria below. Local sealing/push is authorized before G2; G2 retains its sequential processing and review boundary.

## Final G1 acceptance check — 2026-10-21

- Regenerated Batch 1: **Partial**, exit **0**. Candidate SHA-256 `12f14f34275cd712c3ac1551a30e6358cbca67bf1cea51cf053dd12a86a62932`.
- **Full regression suite, run once:** `python3 -m unittest discover -s tests -v` — **140 passed**, including eight refusal-action regressions.
- All six actual refused decisions now have exactly one MSP-owned action containing the source decision ID and first refusal reason; each new action has null due date. Equivalent existing actions/deadlines are reused, including terminal files; repeat projection creates no duplicate or source mutation.
- Existing G1 criteria pass: complete snapshot and retained history, 40 applications / 41 revisions, all current caseload entries, full unchanged schema/date-format and cross-record validation, complete produced inventory, six source decision records/refusals retained, owned evidence work and run log, and the previously independent **219-day** calendar result still matches. No ready packets, approvals, activations or executed outreach.
- Comparison with the preceding candidate: only six escalation actions added. Existing actions, clocks, statuses, evidence, decision outcomes, full history and packets are unchanged. All 46 protected input/source/interview/schema/instruction/archive files retain their hashes.
- **Exception assessment, separate from validation:** the [owner-approved Q07 exception](rules.md#q07-owner-approved-semantic-exception) is accepted for G1 by the current owner instruction; original schema wording and the stakeholder/source conflict remain unchanged. Structural checks do not certify compliance with that wording.
- No new material failure. Conditional owner acceptance therefore applies. Proceed with G1 sealing/push and then the existing G2 sequence: checked Batch 2, local Batch-2 seal, fresh-process Batch 3, stop for G2 review. No final G3 acceptance or Batch-3 sealing is inferred.

The earlier results below remain historical checkpoints.

## Owner exception focused verification

- Candidate: [snapshots/batch-01.json](snapshots/batch-01.json), as of **2026-03-16**, **40 applications / 41 retained revisions**. SHA-256: `1b3445ad80c86624821975f69df199a9852411477b1c457a1b9f2f254385c9d9`.
- Actual command: `python3 -m credentialing run --batch inputs/batch-01 --sources sources --output deliverables --batch-number 1`; execution recorded in the append-only [run log](run-log.md).
- **Structural validation:** full candidate passes unchanged Draft 2020-12 schema with date-format checking. Existing `validate_snapshot` cross-record checks pass, including complete unique caseload, latest revisions, source decision inventory, consumed files and first-batch predecessor.
- **Focused semantic checks:** exactly **38 application status fields** changed from null to `intake-incomplete`; every other application field is unchanged. Entire history and packets are unchanged against the pre-change baseline, including raw records, missing evidence, actions, actual notices and refused decisions. All 38 affected cases have no intake notice and retain an explicit pending MSP dispatch action with null due date.
- **Actual clocks:** APP-2026-019's release/CV actions keep **March 20**; pending signature/referee-name work remains null-due. APP-2026-018 keeps its actual return and **April 5** deadline. Status totals are **39 intake-incomplete / 1 returned-incomplete**; **six recommendations refused, zero ready packets, approvals or activations**.
- **Regressions: 68 pass** across intake (9), engine (13), decisions (12), dates (10), Q07 (6) and IO (18). Commands: `python3 -m unittest discover -s tests -p test_<module>.py -v` for `intake_evidence`, `engine`, `decisions`, `dates`, `q07`, `io`. This is a focused pass, not a rerun of every module.
- Synthetic boundaries distinguish pending dispatch even months later, actual clock through its due day, expiry the following day, fulfilled older requests with newly pending items, and unresolved notice coverage. Positive evidence/decision fixtures remain synthetic; no source events were added. Unsupported null-status output still reports Blocked/exit 2 in IO tests.
- **Contract exception:** the Q07 tests deliberately assert that S still requires an already-written request and running clock. Mechanical validity does not resolve that discrepancy; the canonical owner decision linked above governs this candidate.
- **Preservation:** all 46 baselined source/input/interview/schema/instruction/archive files retain their hashes. Existing run-log bytes remain an unchanged prefix. Schema SHA-256 remains `df371cfd4638194348be79352a0683d9d4dc40bb4f95d87f6028a7b889274318`.
- **Review boundary:** candidate only; no G2, sealing, commit or push. Practitioner evidence and human decisions remain owned casework, not new acceptance claims. The [local package scan](skill-scan.md#q07-owner-exception-follow-up-scan) retains its documented findings.

## Historical checkpoints

All sections below retain earlier observations, including superseded Blocked/no-snapshot handling and earlier test counts. They do not describe the current candidate. Prior source comparisons remain evidence of the unresolved original wording.

## Commands and observed results

The 85-test and original-run observations below are historical G1 evidence. Prior correction verification: **129 targeted tests passed**, actual run exits 2 with `blocked_stage: snapshot-production`, parsed inputs and retained diagnostics; no contract-complete Partial outcome is claimed. Positive synthetic evidence now clears previously unconditional checks while actual evidence gaps remain. Source comparison, precise corrections and parser limits are in [g1-review-response.md](g1-review-response.md).

```bash
python3 -m unittest discover -s tests -v
python3 -m credentialing run --batch inputs/batch-01 --sources sources --output deliverables --batch-number 1
```

- **85 focused tests pass**: date boundaries, accepted-source/revision/provenance checks, peer cadence, certification/training/eligibility, decision authority/order, schema dates, malformed/missing inputs, protected sealed output, exact activation grants/dates, and real batch-1 checks.
- Real run command/execution timestamps/consumed and written files are recorded for every invocation in [run-log.md](run-log.md). Source checks identified an omitted-middle-name matching bug after the first run; subsequent runs use the corrected exact first/last-name match with optional declared middle name. The original run entry is retained.
- A tightened conditional-approval check exposed a synthetic fixture lacking dated conditions. The fixture now supplies explicit conditions for its positive case; a separate negative test retains the missing-date refusal. No real approval was invented.
- Repeated identical invocations produce byte-identical working results, history, packets and run metadata; the run log appends the new attempt. Processor and rules changes invalidate the fingerprint. Source bytes are checked against both capture manifests.

## Actual source-to-result checks

| Check | Evidence | Observed result |
| --- | --- | --- |
| Complete input and caseload | 13 CSVs, 1,631 data rows; 15 indexed documents; original export README; capture manifest | 41 application revisions / 40 unique files retained; every indexed path read; six standing sources captured with provenance |
| Required evidence remains owed | applications.csv lacks application signature/date evidence and CV text; verification/peer exports lack accreditation/direct-return evidence | All 40 packets remain not presentable; no inferred verification, approval or activation |
| Intake clocks and returns | APP-2026-019 letter dated 2026-02-18; APP-2026-018 return dated 2026-03-06 | `intake-incomplete`, due 2026-03-20; `returned-incomplete`, due 2026-04-05; no verification outreach without signed release |
| Schema limitation Q07 | Other 38 files lack a recorded applicable incomplete notice | Internal status null, explicit pending dispatch and limitation; no public snapshot emitted |
| Finding plus discrepancy | APP-2026-015 WA credential MD60069441; board-action letter; PPQ-1 No | Restriction finding and disclosure discrepancy both retained; licensure summary outstanding; applicant/CD actions remain |
| Primary-source rejection | APP-2026-020 applicant-carried degree; APP-2026-022 medical-society reply | Received records retained; no acceptance from applicant or unlisted society |
| Possible secondary route | APP-2026-021 ATT-2104 closure and ATT-2105 FCVS no record | MSP assessment queued with attempt refs; no blanket secondary-source authorization or inferred accreditation |
| Five-year/revision anchor | APP-2026-025 revisions 1 and 2 | Latest revision 2, original 2024-04-22 receipt retained, prior assessments/evidence preserved |
| Contested dates | APP-2026-030 declared versus verified end date | Both values retained; entry unresolved; any gap arithmetic labelled provisional |
| NPI versus state licence | APP-2026-031 declaration/WA lookup/letters | NPI does not satisfy missing WA licence; other-state observations retained |
| Actual committee records | MEC-2026-011/013/017/023/024/034 | All six preserved and refused for first failed check 4, prior presentability; positive recommendation needs no reason; authority itself is established |
| Readiness/activation | All actual applications | 0 ready, 0 admitted approvals, 0 activations; no reserved judgment made |

## Independent calendar recomputation

The following arithmetic was performed with calendar month lengths, without importing or calling any Skill date helper.

1. **APP-2026-017:** `inputs/batch-01/declared-history.csv` entries ENT-1702/ENT-1703 end **2019-03-31**; ENT-1704 starts **2019-11-06**. The uncovered interval is **2019-04-01 through 2019-11-05**, inclusive. April 30 + May 31 + June 30 + July 31 + August 31 + September 30 + October 31 + November 5 = **219 days**. The February 13 explanation covers that interval, but 219 ≥ 180 requires a recorded Clinical Director disposition. B1 supplies none. `working/batch-01/history.json`, application APP-2026-017, latest `assessments[].gaps.gaps` reports **219**, with explanation source and CD hold: **match**. No later memo or missing February 24 explanation from later batches was imported into B1.
2. **APP-2026-005:** ENT-0501 ends **2013-06-30**; ENT-0502 starts **2013-07-31**. The uncovered July dates 1–30 total **30 days**. Its February 6 explanation covers the full interval. The result reports **30**, with the explanation and no long-gap CD hold: **match**. Its unrelated evidence deficits still prevent readiness.
3. **Recorded deadlines:** February 18 + remaining 10 February days + 20 March days = March 20 (30 days). March 6 + remaining 25 March days + 5 April days = April 5. Both match the actual letters and computed actions. The due day is included; no pending dispatch created a clock.

## Schema, history and safety

The original Draft 2020-12 schema and all original interview/instruction files retain their starting SHA-256 hashes. Application shapes are checked against the schema with date formats enabled; only the explicitly internal null-status exception is allowed in working artifacts. **This is not a passed public-snapshot validation.** `results.json` is a working result, not `snapshots/batch-01.json`.

Rich history preserves raw CSV rows, original document text, current/prior revisions, attempts, received evidence, all decision failures and historical pre-decision assessments. Packets are labelled evidence summaries, not presentation events. No future batch evidence is read. Batch>1 is rejected at this gate. Positive activation/conditions have synthetic coverage only; actual B1 contains recommendations and no GB grant. Continuation, actual later dispositions, post-activation renewal/satisfaction and full three-batch acceptance remain G2/G3 work.

The local Skill scan and manual dispositions are in [skill-scan.md](skill-scan.md). No install or cloud analyzer was used. Runtime dependencies are pinned to the installed/tested jsonschema 4.19.2; Python here is 3.14.4. No code, source file or snapshot was committed or pushed during this turn.

## Owner review boundary

Review the retained cases, actions and implementation. The remaining G1 acceptance blocker is a truthful public representation for the 38 pending-dispatch holds under unchanged S. Evidence gaps remain casework, not implicit passes. Source format limitations and unknown edge policies remain explicit. The processor has not hidden this incompatibility behind valid-looking status values or dropped files. No G2 work or sealing proceeds without the existing gate approval.

## Focused troubleshooting follow-up

See [focused findings](g1-troubleshooting.md), [APP-2026-001 source trace](g1-evidence-trace.md) and [exact Q07 probes](g1-q07.md). **64 targeted tests pass** after action/deadline attribution and unsupported Q04 wording corrections. The prior 85-test result above is the original G1 run, not a claim that the full expanded suite was rerun during this pass. Three logged CLI invocations refreshed batch-1 working outputs; no schema, evidence or acceptance status changed. APP-2026-019 keeps its actual March 20 clock for release/CV, with separate null-due pending signature-evidence/referee-name work. Q07 remains the complete-snapshot blocker.
