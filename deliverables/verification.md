# Gate verification

**Current result: G3 corrections accepted; corrected chain sealed locally, final push review pending.** All three supplied batches and required processing artifacts are complete and consistent: **Supported with the accepted Q07 exception**. Individual batch outcomes remain Partial because legitimate practitioner evidence and human decisions are unsettled. No push performed. Capture is owner-managed, not newly verified by the agent.

## Final corrected-chain promotion — 2026-10-21

The owner explicitly accepted the G3 corrections and authorized this local correction/sealing sequence. No new discovery, policy changes or comprehensive review were performed. Runtime code, rules, schema and supplied evidence are byte-identical to the reviewed candidate inputs.

| Batch | Actual sealing commit | Snapshot SHA-256 |
| --- | --- | --- |
| 1 | `85377cc1d1be85c6ee631a418dcf8b455032fdee` | `1cf9267f487d4e1a3541d6d61aa93d18d16273fbc43bba51cacbb1ed2a1a723e` |
| 2 | `65943677d4b535de83e0ec7d8a5dfaa58956112f` | `9fb37f39bbe58cb36a144d2c381d2b1c41c49208af81932f8bd4ef7c83e11cf5` |
| 3 | `d0e26f5fcabc07e7863c5af66f001696cb30f6d7` | `b32fcf24dc1e26a89137a5c414276018d599de6fba2ac57a89268e19f20dadf9` |

Snapshot IDs: `batch-01-bfbc29875e841e72c2e1`, `batch-02-d193d44b5fa4b91b9766`, `batch-03-855c7010462e4a4c5aba`. Each canonical snapshot and its four matching working files equal both the reviewed candidate bytes and the exact sealing commit. Git ancestry confirms sequential commits. [Machine-readable final validation](g3-promotion-validation.json) records these checks.

### Actual sequence and validation

1. Verified all 15 originals against [archive hashes](archive/pre-g3-correction/manifest.json); preserved original and frozen review packages unchanged. Explicitly promoted B1 plus four working files, checked schema/date/cross-record invariants and recomputed code/rule/input/source/schema fingerprint, then sealed it. The normal B1 CLI verified an unchanged sealed rerun against actual Git bytes.
2. Promoted B2 plus four working files. Production predecessor loading verified newly sealed B1, matching state and retained history; fingerprint/schema/output checks passed before the B2 seal. Its normal CLI then verified an unchanged sealed rerun. These two promotions are not claimed as new CLI recomputations.
3. Ran B3 in a **fresh Python process**, using actual corrected sealed B2. Production returned Partial/exit 0; the snapshot and all four state files matched the reviewed candidate byte-for-byte. Validated the full chain before sealing B3. Its subsequent normal CLI rerun returned Partial/exit 0/`unchanged: true`, writing only the run log.
4. Final checks pass: unchanged schema with date formats, complete 40-application caseload/latest revisions, source decision inventory, exact history prefixes and predecessor state hashes, all artifact fingerprints, unique MSP refusal actions with IDs/reasons and no invented deadlines, and all required paths. All **176 protected source/input/interview/schema/rule/archive/review files** remain unchanged from the start of promotion; original run-log prefix retained. All 15 canonical snapshot/state files equal their seal commits and final chain HEAD.
5. **Full regression suite once after promotion: 237 passed in 6.385s** — [log](g3-promotion-regression.log). Only two test constants were updated to the accepted corrected predecessor hashes; archived-original checks remain unchanged. Existing malformed-input, tamper, unchanged-rerun, connected positive/condition and authority-boundary coverage passed; no new production mode or tests were needed.
6. Recomputed APP-017's inclusive gap independently with standard-library dates: `(date(2019,11,5)-date(2019,4,1)).days+1 = 219`; matches all three corrected histories. This does not substitute for the missing specifically dated explanation. [Final package scan](skill-scan.md#final-promotion-handoff-scan) retains explicit finding dispositions, not a clean-scan claim.

### Real results, synthetic coverage and remaining limitations

- **Real exports:** 40 applications; 41 → 45 → 46 revisions; 6 → 35 → 56 decisions, all refused with owned MSP actions. No real readiness, approval or activation. Statuses/decision outcomes remain identical to archived originals. APP-021 no-record blank dates create no false contradiction/provisional-gap hold; required education/accreditation and MSP exception determination remain outstanding. APP-020's cured source-rejection work and APP-025's carried-referee correction match the reviewed package. APP-019 March 20 and APP-018 April 5 clocks remain unchanged; pending dispatch keeps null deadlines.
- **Synthetic coverage:** the connected qualifying-evidence → revision readiness → MEC → GB → exact authorized activation workflow, including conditions and named satisfaction, passes. Synthetic fixtures establish no practitioner qualifications or real approvals.
- **Accepted exception, separate from validation:** [Q07 decision and assessment risk](rules.md#q07-owner-approved-semantic-exception) remain unchanged. Structural/behavioral success does not certify compliance with the original schema-description wording or resolve the stakeholder/source conflict. Status alone establishes no dispatch, expiry, readiness or approval.
- **Retained limits:** real missing evidence/Q17 conflicts, unsupported narrative formats and reserved human judgments remain owned casework in the [tracker](../PROJECT-TRACKER.md). Existing bounded policy residuals and original-byte/source-checksum limits remain. Owner handles capture and eventual submission association; this work neither repairs nor verifies Entire coverage. No new token total is available because no push occurred.

The frozen rule register's opening gate prose and frozen replay report's pending/unsealed flags describe the earlier review checkpoint. This current record and tracker supersede that lifecycle wording; computational rules and candidate fingerprints are intentionally unchanged. The following sections are historical checkpoints, not current seal status.


## G3 final verification — 2026-10-21

### Real-batch evidence and corrections

[Replay report](corrections/g3-review/report.json) and [candidate outputs](corrections/g3-review/candidate/deliverables/) contain the proposed corrected chain. Exact original snapshots/state are preserved in [pre-correction archive](archive/pre-g3-correction/manifest.json) and at their canonical paths. All 158 protected baseline files (including original inputs, sources, interviews, schema, instructions and 15 snapshot/state artifacts) retain their hashes. Canonical run-log history is preserved as an append-only prefix. Real Git comparisons confirm both sealed predecessors still equal `HEAD`.

| Export | Applications / revisions / decisions | Correction to public application fields |
| --- | --- | --- |
| Batch 1, March 16 | 40 / 41 / 6 | APP-025 actions: carry two named referees into revision 2; remove unsupported name request, retain direct-return-provenance work. |
| Batch 2, April 20 | 40 / 45 / 35 | APP-021 actions and gap state: remove fabricated date discrepancy/provisional timeline hold. |
| Batch 3, May 18 | 40 / 46 / 56 | APP-021 as above; APP-020 obsolete rejection action becomes retained-material work after valid VR-2003. |

All application statuses and public decision records/reasons are unchanged. There are **zero real ready packets, admitted approvals or activations**. Latest statuses remain 36 intake-incomplete and one each returned-incomplete, ineligible-clock-expired, withdrawn and discontinued. All 56 real refused decisions retain exactly one MSP action containing ID/reason. Genuine intake/CV/accreditation/peer provenance requirements, Q17 source conflicts, APP-015's missing numbered correction and actual notice deadlines remain.

**APP-021 trace:** B2 `verification-replies.csv#VR-2104` is FCVS `no-record`, with both verified dates blank. E/B36 says these are absent held values, not facts contradicting declared ENT-2100 dates 1998-08-24–2002-06-30. The prior implementation compared those blanks and generated both a false date discrepancy and a downstream provisional-gap action. Corrected code distinguishes missing boundaries from competing values; confirming replies still need required boundaries. VR-2100's dated secondary-source account, recorded closure, FCVS no-record and all attempts remain. ENT-2100 has no accepted verification, accreditation remains absent, and MSP still owns the documented-impossibility/secondary-route determination. Gaps resolve on the declared timeline; the application does not become ready. Actual nonblank contradiction and explicit discrepancy controls still block.

**APP-020 trace:** B3 VR-2003 is now the usable direct school reply. Earlier applicant-routed VR-2000 stays in raw history and rejection checks, with a nonblocking retained-material action instead of an obsolete current request. Accreditation remains missing. Neither rejection retention nor a later date is treated as a permanent readiness bar or as a new source-acceptance rule.

### Synthetic coverage and comprehensive review

A single comprehensive **Astra High** pass and focused follow-ups are recorded in [g3-final-review.md](g3-final-review.md). All six findings are corrected: blank-date contradictions; named condition satisfaction; surplus-reference holds; rejected-reply cures; PPQ mention mistaken for a returned human disposition; and the earlier referee-carry correction missing from sealed Batch 1. No unresolved material runtime finding remains from that review. The explicit conditional/negative PPQ controls prevent a signed “under review”, “do not present”, “after review” or “if cleared” document from clearing the hold.

The former positive activation tests injected an already-ready assessment. New `tests/test_connected_workflow.py` supplies explicitly synthetic signed application/CV, accepted credential/accreditation evidence, WA licence, qualifying direct peers and rostered MEC/GB records, then calls the actual `process_batch` path. It proves computed evidence → readiness → same-revision recommendation → approval → exact privilege activation, including future effective date, conditions and WA expiry. It also proves same-day evidence cannot retrospectively admit the recommendation/approval, and a surplus request closes only after recorded presentation.

`tests/test_condition_satisfaction.py` exercises the connected conditional case: an overdue condition has a CD action; an explicit qualified record naming that condition removes only that obligation/action, preserves original approval conditions and source history, and leaves activation/other conditions unchanged. Unnamed, mismatched, future, unsigned or unsupported records do not clear it. The bounded parser's supported CD/routine-MSP format is an engineering limit, not an invented office authority rule; see [rule notes](rules.md#g3-implementation-clarifications). These synthetic records are never written into real batch inputs or candidates.

### Executed checks

- **Full regression suite:** `python3 -m unittest discover -s tests -v` — **237 passed, 7.212 seconds**. Run after final runtime corrections. Focused tests during development exposed and corrected a test-module import incompatibility; both discovery and module invocation now work. The replay helper's later archive-log adjustment was exercised by replay without altering runtime behavior.
- **Structural and semantic validation:** all three preserved snapshots and all three corrected candidates pass unchanged Draft 2020-12 with date formats. Candidate cross-record validation, complete caseload/latest revisions, real source decision inventory, one owned action per refusal, output inventory, code/rule/source fingerprints, working-output hashes, predecessor hashes and exact history prefixes pass.
- **Real-source replay:** `python3 tests/replay_batches.py` successfully processes all 39 CSVs / 1,945 rows / 82 indexed documents, one fresh interpreter per export. It uses production engine/IO with only the Git checkpoint boundary replaced by a clearly labelled byte-backed test double. The intermediate candidates are validated before the next process. Repeated unchanged replay preserves checked bytes; malformed actual input copy and tampered predecessor are rejected while prior checked snapshots remain unchanged. Candidate logs and detailed failures are retained in the package/report.
- **Actual production seal guard:** the current-code Batch-1 CLI was deliberately invoked against its real sealed occurrence. Expected **Blocked/exit 2**, `Sealed snapshot cannot be overwritten`, no snapshot emitted, only the run log appended. All sealed/candidate originals retained. This proves overwrite protection; it is not a failed corrected-batch computation or a successful supersession.
- **Independent quantity:** direct standard-library calendar subtraction, `(date(2019,11,5)-date(2019,4,1)).days+1`, independently gives **219 days** for APP-017, matching all three corrected histories and the previously documented source calculation. It does not call the Skill's date helper or resolve the missing February 24 explanation.
- **Skill package scan:** pinned local scanner 2.0.13, exit 1, same two argv false positives plus file-count/license findings; dispositions in [scan report](skill-scan.md#g3-handoff-scan). No clean-scan certification claimed.

### Unresolved limitations and acceptance work

1. **Q07 exception:** [canonical owner decision](rules.md#q07-owner-approved-semantic-exception) is byte-equivalent to the prior recorded section. It was not reopened. Passing validation does not establish compliance with the original status description or resolve stakeholder/source wording.
2. **Correction lifecycle:** all corrected occurrences have new IDs and linked hashes, but are staged and unsealed. Simulated checkpoint replay is not a claim of actual continuation from newly sealed corrected predecessors. The [concrete promotion sequence](../README.md#production-sequence--after-explicit-acceptance-and-sealing-authorization) explicitly handles both already-sealed Batch 1 and Batch 2, verifies actual Git state after authorized promotion/sealing, then requires an actual fresh-process Batch-3 regeneration. Those steps remain pending authorization.
3. **Capture:** read-only `entire status` / `entire doctor` report enabled capture, installed/approved hooks and elected `origin`, but one session remains marked active after its process exited, with pending turns. Two configured remotes also require confirming the elected destination. No `--force`, condensation, repair, commit or push was performed. Owner/facilitator must reconcile coverage and association with the eventual submitted revision; neither self-written logs nor counters prove completeness.
4. **Evidence/parser limits:** real gaps and conflicts remain owned practitioner casework, not proof of disqualification. Source captures and original-byte checksum limits, unsupported narrative formats, bounded policy residuals and reserved clinical decisions remain as documented. No real positive approval is demonstrated by these supplied exports.

## G2 review checkpoint — 2026-10-21

| Export | Retained applications / revisions / decisions | Run and seal |
| --- | --- | --- |
| Batch 1 — March 16 | 40 / 41 / 6 | Partial; accepted, sealed and pushed `013fde1` |
| Batch 2 — April 20 | 40 / 45 / 35 | Partial; checked and locally sealed `e711140` |
| Batch 3 — May 18 | 40 / 46 / 56 | Partial; fresh-process resume, unsealed review candidate |

**Validation results:** all three snapshots pass the unchanged Draft 2020-12 schema with date-format checking; new B2/B3 invocations also pass existing cross-record checks. Batch 3 references sealed Batch 2 SHA-256 `787c50ce2d8fa014f3a68abc83dd68dcd9813220fd8c0297a411b9860fbd4383`, which references the exact sealed B1 hash below. Batch-3 candidate SHA-256 is `a98b1f22124f8c44a50afa04956cb9fa29d4189c282a6c9e3e7002444815e63f`. All 10 prior snapshot/state files equal committed bytes; all 46 protected source/input/interview/schema/instruction/archive hashes match; the run log retains its prior committed prefix. Produced files and rules links resolve.

**Actual sequence:** B2 was checked and locally sealed before B3 capture/processing. Its unchanged sealed rerun reported Partial/exit 0/`unchanged: true`, writing only the run log. Then the separate shell invocation `python3 -m credentialing run --batch inputs/batch-03 --sources sources --output deliverables --batch-number 3 --predecessor deliverables/snapshots/batch-02.json` resumed from sealed state, followed by unsealed regenerations for the corrections and rule-source note. Each invocation is in the [run log](run-log.md). B3 captured 40 originals: 13 CSVs/100 rows, 26 indexed documents and README; [manifest](../inputs/batch-03/manifest.json) records original-byte hashes and the independent-source-checksum limitation. Across all three exports: **39 CSVs, 1,945 rows, all 82 indexed documents** retained.

**Focused regression results:** `python3 -m unittest tests.test_engine tests.test_evidence tests.test_history tests.test_revisions tests.test_dispositions tests.test_continuation tests.test_io tests.test_g2_batch2 tests.test_activation tests.test_decisions tests.test_g2_batch3 tests.test_refusal_actions tests.test_q07` — **168 passed**, 6.066 seconds. This is G2 focused integration, separate from the once-run 140-test G1 full suite. Actual B3 assertions cover complete caseload, 46 revisions, all 56 real decision IDs/refusals and their unique MSP actions, exact history prefixes, original first receipts, stale peers, source conflicts, revised privileges and reserved judgments. Synthetic tests exercise positive activation, exact approved subset, effective-date/cycle calculations, conditions and explicit supersession; they are not evidence of actual applicant approval.

**Corrections and source outcomes:**

- B2 corrections and case checks remain in the checkpoint below. No earlier sealed output was rewritten by the B3 changes.
- APP-015's actual May 6 CD disposition is qualified against roster/signature and the specifically dated March 4 board summary/April 20 applicant confirmation. The restriction remains a finding, with MSP responsible for packet inclusion; the conflicting PPQ-1 No remains unchanged and Applicant owns the missing numbered correction revision. Removing either referenced record or CD authority prevents disposition qualification. No recommendation/approval or unrestricted licence is inferred.
- APP-027's April 27 revision 2 requests family medicine; that exact revision is assessed and the old amendment-choice action is not repeated. Certification source-date conflict and other evidence gaps remain.
- APP-025's May 5, 2024 reference is stale on May 18, 2026; May 20, 2024 remains current. Missing direct-return provenance remains. [Source-boundary wording conflict](rules.md#g2-source-application-notes) is retained separately; the existing inclusive B19 rule is unchanged and neither export falls on the disputed anniversary.
- VR-3604 is retained only on ENT-3602 (2012–2019), not transferred to unchanged ENT-3603. Q17's revision-prose conflict remains; attachment does not imply that the older out-of-scope entry was newly verified. APP-017's specifically missing February 24 explanation and APP-018/034 identity/employer conflicts remain.
- A synthetic admitted approval followed by an explicitly superseding denial/deferral exposed retained old approval/activation/conditions. The projection now clears that superseded authorization; all seven activation tests and twelve decision tests pass. Actual supplied approvals remain refused, so this correction changes no supplied decision outcome.
- Batch 3 has **36 intake-incomplete, one returned-incomplete, one ineligible-clock-expired, one withdrawn, one discontinued**. All 56 decisions remain refused; **zero ready packets, approvals or activations**. APP-019's actual March 20 deadline and APP-018's actual April 5 return remain; pending dispatch has null due dates. No outreach was executed.

**Documented contract exception — not a validation result:** [Q07's owner-approved semantic exception and remaining assessment risk](rules.md#q07-owner-approved-semantic-exception) remain unchanged. G1 acceptance includes that exception; passing validation does not resolve stakeholder/source wording or certify compliance with the original status description.

**Review boundary:** no unresolved implementation failure from these focused checks. Genuine evidence gaps/source conflicts remain MSP/applicant/CD casework, as summarized in the tracker. Actual session-capture coverage remains the owner/facilitator's G3 handoff check. Batch 3 is unsealed; no G2 push, G3 work, final handoff or overall Supported claim. [Skill scan](skill-scan.md#g2-final-runtime-scan) has explicitly dispositioned findings, not a clean-scan claim.

## G2 continuation — Batch 2 checked before local seal

G1 is sealed and pushed at `013fde1`. Batch 2 was processed only afterward; Batch 3 has not yet been consumed at this checkpoint. G2 owner authorization includes this checked local Batch-2 seal, then fresh-process Batch 3 and a review stop.

- Command: `python3 -m credentialing run --batch inputs/batch-02 --sources sources --output deliverables --batch-number 2 --predecessor deliverables/snapshots/batch-01.json`. Final unsealed regeneration: **Partial, exit 0**. [Run log](run-log.md) retains both actual invocations.
- Captured **55 original files: 13 CSVs / 214 rows, 41 indexed documents and README**, with raw-byte hashes in [manifest](../inputs/batch-02/manifest.json). A signed-download delay was resolved using the connector's explicit raw-byte base64 export; no document text was reconstructed.
- **Structural/date-format and existing cross-record checks pass**: 40 applications, 45 retained revisions, 35 decisions/refusals, zero ready packets/approvals/activations. Statuses: 36 intake-incomplete, one returned-incomplete, one ineligible-clock-expired, one withdrawn, one discontinued. All 35 refusals have one MSP-owned action with ID/reason and no invented deadline.
- **123 focused checks pass**: engine 13, evidence 30, retained history 5, revisions 20, dispositions 12, continuation 11, IO 18, actual Batch 2 checks 14. G1's full suite was run once (140 pass); this is a separate G2 scope. Synthetic tests cover fresh-process resume, tampered/missing predecessor state, deduplication and failure preservation. Actual Batch-3 resume remains the next step.
- Batch-2 SHA-256: `787c50ce2d8fa014f3a68abc83dd68dcd9813220fd8c0297a411b9860fbd4383`; predecessor is the exact sealed Batch-1 hash `12f14f34275cd712c3ac1551a30e6358cbca67bf1cea51cf053dd12a86a62932`. All five Batch-1 snapshot/state artifacts equal committed bytes; all 46 protected hashes remain unchanged. Prior assessments, readiness and decisions remain exact history prefixes; current revisions and original first receipts are retained.
- Corrections during G2 integration: unchanged referee nominations carry across revisions despite header-only selective export; earlier date-discrepancy replies can support an explicitly corrected numbered revision; actual Clinical Director dispositions are parsed with authority and referenced-evidence checks; source conflicts remain owned work. Refused decisions are never retrospectively admitted using later evidence.
- APP-017: April 2 CD judgment retained, but specifically referenced February 24 explanation absent; no gap clearance. APP-018: March 30 explanation conflicts with declared employer; actual April 5 return deadline preserved. APP-019: actual March 20 notice expired, while unrequested evidence remains pending/null-due.
- APP-027: April 8 offer to amend is not discontinuation; April 10 certification initial-date conflict retained. APP-028: actual April 6 withdrawal. APP-029: valid March 31 CD discontinuation retained separately from April 2 letter recipient mismatch. APP-030: revised dates reconcile VR-3002, but new ENT-3090 still lacks verification. APP-031: new WA licence/declaration resolves only that evidence. APP-032: April 2 PPQ-2 disposition remains a packet finding, without clearing other holds. APP-034/036: name/period source conflicts retained; future VR-3604 not consumed.
- GBD-2026-039: parser now handles the source's bold Conditions label and distinguishes explicit **November 30 / June 30** due dates from **December 31** licence expiry. Structured refused-decision history retains both conditions; no approval or monitored obligation is inferred from a refused record. APP-025's May 5/20, 2024 signatures are still current on April 20, 2026; missing direct-return provenance remains outstanding.
- **Contract exception, separate from validation:** [Q07 owner decision](rules.md#q07-owner-approved-semantic-exception) is unchanged. Passing structure/semantic checks does not establish compliance with the original pre-dispatch status description. Practitioner evidence deficits are separate casework.

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
