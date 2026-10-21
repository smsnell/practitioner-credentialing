# Practitioner credentialing — operational tracker

Updated: 2026-10-21. Current operational status only; business clock remains the batch export date.
[Unchanged pre-compaction archive](PROJECT-TRACKER-2026-10-21-G1-ARCHIVE.md) retains prior decisions, source references, metrics and review history.
Archive SHA-256: `b6bfb6a5cb05a0dfb4e33a0af9a35b4fe045207ff922c408ab1306cbee5222c6`.
Historical “Partial without snapshot” reports and earlier test counts are superseded, not current acceptance evidence.

## Gate, authorization and acceptance

- **Gate:** G3 corrections accepted; corrected B1–B3 chain promoted and sealed locally. Original occurrences and reviewed package preserved unchanged.
- **Acceptance:** all processing gates complete; **Supported with accepted Q07 exception**. Final suite **237 passed**; individual batches remain Partial. No new material failure.
- **Current authorization:** local promotion/sealing and final handoff completed. **Stop before pushing for owner review.** Owner handles capture; no agent repair or capture-confirmation claim.
- **Lifecycle:** corrected seals B1 `85377cc`, B2 `6594367`, B3 `d0e26f5`; final documentation commit follows. `origin/main` remains `013fde1`; no push. Schema, evidence and architecture unchanged.
- Architecture, scope and acceptance gates remain in [IMPLEMENTATION-PLAN.md](IMPLEMENTATION-PLAN.md#2-preconditions-and-proposed-gates).
- Deliverable/outcome authority: [REQUIREMENTS.md](REQUIREMENTS.md); status meanings: [snapshot.schema.json](snapshot.schema.json).
- Rules and sources: [applied-rule register](deliverables/rules.md). Model/effort and bounded delegation: [ORCHESTRATION.md](ORCHESTRATION.md).

## Q07 contract exception

**Owner: project/contract owner.** Q07 remains distinct from practitioner evidence and decisions.
The [single decision record and remaining assessment risk](deliverables/rules.md#q07-owner-approved-semantic-exception) govern the sealed corrected chain.
The mapping blocker is addressed by owner authorization; original schema-description compliance and stakeholder reconciliation are **not** established.
Structural/behavior checks and exception acceptance are reported separately in [current verification](deliverables/verification.md#final-corrected-chain-promotion--2026-10-21).
[Prior source comparison](deliverables/g1-review-response.md#new-clarification-and-q07) and [historical incompatibility proof](deliverables/g1-q07.md) remain preserved.

## Practitioner casework — separate from Q07

**Operational owner: MSP (Renata Kowalczyk)**; applicant supplies corrections/documents, Clinical Director retains reserved judgments.
These are preserved evidence deficits or conflicts, not proof of missing qualifications and not permission to resolve human decisions.
The casework below describes the current corrected sealed Batch 3 (May 18). Superseded outputs remain archived and are not current results.

| Scope / case | Outstanding work and owner |
| --- | --- |
| Batch-wide evidence | MSP obtains application signature/date evidence, actual CV contents for reconciliation, required accreditation and direct peer-return provenance. Existing receipt/degree/training/eligibility facts remain retained; absence from the export is not proof of absence in the office. |
| APP-2026-019 | The existing February 18 release/CV notice expired after **March 20**; APP-019 is ineligible-clock-expired. MSP's new signature-evidence/referee-name requests remain pending with null due dates. Verification outreach remains held for release. |
| Q17 / APP-2026-036 | MSP/applicant reconcile revision prose naming 2019–2025 against changed ENT-3602 (2012–2019); retain VR-3604 on its entry and unchanged ENT-3603. |
| Q17 / APP-2026-034 | Applicant/MSP resolve Ingrid Solheim versus Ingrid Lindholm correspondence identity; no clarification or dispatch is inferred. |
| Q17 / APP-2026-017 | MSP obtains the specifically referenced **February 24** explanation; February 13 cannot substitute. CD disposition must match its evidence. |
| Q17 / APP-2026-018 | Applicant/MSP reconcile Harrowgate versus Silverbeck. Preserve the actual March 6 return and April 5 deadline. |
| APP-2026-021 / 020 | MSP still owns APP-021 secondary-route/impossibility determination and missing accreditation. FCVS no-record blanks are not a date contradiction. APP-020 valid VR-2003 resolves earlier source-rejection work; accreditation remains missing. |
| APP-2026-015 | Applicant/MSP obtain the numbered correction revision; April 20 confirmation and May 6 CD disposition do not replace it. Restriction finding remains for MSP packet inclusion; declaration discrepancy remains Applicant-owned. |
| GBD-2026-038 / 035 | MSP retains the missing valid same-revision Executive recommendations; unauthorized MEC approval or a revision-1 recommendation cannot satisfy the dependency. No approval inferred. |
| GBD-2026-039 / Q16 | MSP retains November 30 / June 30 conditions in refused-decision history, separate from December 31 licence expiry; no admitted approval means no active monitored conditions. |
| APP-2026-025 / 027 | MSP refreshes stale peer evidence/direct-return provenance; May 14 letter has anniversary wording conflicting with P/B19. APP-027 family-medicine revision is retained; certification initial-date conflict remains. |

Case evidence/verification targets: [implementation plan](IMPLEMENTATION-PLAN.md#5-focused-verification-matrix); detailed source associations and transcript spelling/ID differences: [archived issue register](PROJECT-TRACKER-2026-10-21-G1-ARCHIVE.md#5-g0-reassessment-and-remaining-issues).
Referee addresses remain explicitly not assessable. No attestation or broad “clean file” claim supplies missing underlying facts.

## Other bounded residuals and handoff obligations

- **Policy/contract owner, if encountered:** Q04 partial-duration arithmetic; Q05 backdate/version boundaries; Q06 receipt/completion timing; Q07 late-cure reopening; Q09 post-activation consequences; Q10 leap-day/designation boundaries.
- Preserve affected holds rather than inventing policy, dates or automatic suspension. These are not new investigation tasks or blanket case blockers.
- **Owner/facilitator — Q13:** owner explicitly handles Entire/capture and submission association. Historical diagnostics are retained; no new investigation, repair or coverage verification. This does not block the authorized local seals.
- Detailed limits and source-document defects remain in [archived residuals](PROJECT-TRACKER-2026-10-21-G1-ARCHIVE.md#bounded-residuals-and-execution-prerequisites); gate obligations remain in the plan.

## Latest verification and retained output

- **Final promotion:** full regression suite **237 passed (6.385s)**; corrected canonical schema/date/cross-record, exact commit bytes, fingerprints and complete-chain checks pass. [Final results](deliverables/verification.md#final-corrected-chain-promotion--2026-10-21); [Astra High review](deliverables/g3-final-review.md).
- Real-source corrected replay: **40 applications throughout; 41 → 45 → 46 revisions; 6 → 35 → 56 decisions**, all refused with unique MSP actions. All 39 CSVs / 1,945 rows / 82 documents retained. Statuses and decision outcomes unchanged; zero real ready packets/approvals/activations.
- Real corrections: B1 APP-025 carried-referee actions; B2/B3 APP-021 false discrepancy/gap hold; B3 APP-020 obsolete source-rejection action. Genuine evidence holds remain.
- Synthetic connected tests compute evidence → readiness → MEC → GB → exact activation/conditions; named satisfaction, surplus peers and negative/conditional CD records have controls. Synthetic facts establish no real approval.
- Actual B1/B2 promotion validated against sequential Git seals; fresh-process production B3 matches all five reviewed artifact bytes. All three sealed reruns pass unchanged; full-suite failure guards pass. Independent **219-day** calculation matches all snapshots.
- All **176 promotion-baseline files** unchanged, including original inputs/sources/interviews/schema/rules and archive/review packages; run-log prefix preserved. All 15 canonical snapshot/state files match exact sealing commits. [Pre-correction archive](deliverables/archive/pre-g3-correction/manifest.json) holds exact originals.
- [Final Skill scan](deliverables/skill-scan.md#final-promotion-handoff-scan): exit 1; two fixed-list argv false positives, package-size and licence findings dispositioned. No clean-scan claim.

Current artifacts: [canonical snapshots](deliverables/snapshots/), [working state](deliverables/working/), [seal IDs/hashes/checks](deliverables/g3-promotion-validation.json), [final regression](deliverables/g3-promotion-regression.log). Historical review artifacts: [replay report](deliverables/corrections/g3-review/report.json), corrected snapshots [B1](deliverables/corrections/g3-review/candidate/deliverables/snapshots/batch-01.json), [B2](deliverables/corrections/g3-review/candidate/deliverables/snapshots/batch-02.json), [B3](deliverables/corrections/g3-review/candidate/deliverables/snapshots/batch-03.json), [matching state](deliverables/corrections/g3-review/candidate/deliverables/working/), [regression log](deliverables/g3-regression.log), [canonical run log](deliverables/run-log.md).
Sources: manifests [1](inputs/batch-01/manifest.json), [2](inputs/batch-02/manifest.json), [3](inputs/batch-03/manifest.json); [standing sources](sources/manifest.json), [original interviews](interviews/). [README](README.md) owns exact run/replay/promotion commands and limitations.

## Scoped metrics

| Measure | Last recorded scope / value |
| --- | --- |
| Prior recorded turns | **87m38s** through the completed tracker cleanup, including its **5m02s**. |
| Q07 exception implementation | **7m26s** this turn (07:02:11–07:09:37 UTC); **95m04s** cumulative recorded turns. |
| G1 acceptance + G2 continuation turn | **38m54s** through 17:25:44 UTC (start 16:46:50); **133m58s** cumulative recorded turns. Includes capture/tool/approval waits; parallel work not added twice. |
| G3 verification/review turn | **16m56s** through 20:13:15 UTC (start 19:56:19); **150m54s** cumulative recorded turns. Parallel worker time not added twice. No push; no new checkpoint token total recorded. |
| Final promotion/sealing turn | **9m59s** through 20:56:54 UTC (start 20:46:55); **160m53s** cumulative recorded turns. Includes tool/approval waits; measured before final documentation commit. No push or new token metric. |
| Planning push `a710f80` | **6,728,488 tokens** including cache reads; checkpoint `01M5E6YXSCCDRZJQYW467ZWY24`, one session / 63 calls. |
| Metrics push `f2b6bff` | **778,856 tokens** including cache reads; checkpoint `01M5E71WN6VY88GQ128ZXTJ854`, 9 calls; reported separately. |
| Current token/cost availability | G1 checkpoint `01M5FP0KNRPNC6SXGPJZ9XHH02`: **21,454,256 tokens** (723,621 input + 20,615,040 cache reads + 115,595 output), 212 API calls / 2 captured sessions, `committed_checkpoint`. Not a turn-only total; per-worker usage/cost unavailable. |
| Estimates | Owner's 3–4 hours / 50M tokens remain estimates, not targets. G3 review/handoff preparation complete. Authorized promotion/actual-resume checks complete; owner push review remains. No further development estimated in scope. |

Time is measured active-turn wall time including tool waits; inter-turn waiting is excluded and parallel worker time is not added twice.
Token totals include cached reads, are not cost estimates or a guaranteed whole-project total, and are not E-5/G1-only increments.
Breakdowns, capture association and stale-counter caveats: [archived metrics](PROJECT-TRACKER-2026-10-21-G1-ARCHIVE.md#8-progress-estimates-and-metrics).
Report time after each turn and reliable token counters after an authorized push; do not generate a push to obtain metrics.

## Next action and supporting records

1. **Owner:** review local sealed chain and handoff, then explicitly authorize any push. Q07 remains the documented exception; source casework remains owned.
2. **Owner/facilitator:** reconcile actual capture coverage and final revision association before submission.
3. **Agent:** stop; no push authorized. [README](README.md) records the executed correction procedure and exact unchanged-rerun commands.

[Prior review response](deliverables/g1-review-response.md) retains the correction narrative and parser limits; [applied rules](deliverables/rules.md) own rule/source detail; [plan](IMPLEMENTATION-PLAN.md) owns architecture, scope and gates; [README](README.md) owns run instructions.
The archive preserves historical decisions, source references and superseded results unchanged. Original interviews, source captures, diagnostic artifacts and run logs remain preserved.

## Bounded delegation update

G1: Sol 6.1 Medium owned eight refusal-action tests; lead owned projection and the once-run full-suite/acceptance check. G2: Sol 6.1 High owned raw capture, continuation IO/tests and disposition parsing; Sol 6.1 Medium owned referee/history and actual-batch assertions. Lead Astra High retained policy/state integration and sealing decisions. Ownership stayed disjoint; no extra framework or comprehensive intermediate review.
Integration issues found and corrected: selective referee carry, condition-label/explicit-date parsing, qualified CD review, and synthetic superseding nonapproval retaining old authorization. Test expectations were corrected to source facts for APP-025 April currency and VR-3604 attachment (not out-of-scope verification). Signed-download expiry/approval waits were resolved through original-byte connector export. Per-worker tokens/cost unavailable; push metrics above are checkpoint-scoped, not delegated-task totals.

G3 allocation: Sol 6.1 High handled bounded APP-021/evidence-cure changes and connected/condition tests; lead integrated state, replay and handoff. One **Astra High** comprehensive review plus targeted follow-ups found six corrected issues. Integration fixes included test import compatibility and archive-log prefix handling; no extra production mode/framework. Actual metrics remain checkpoint-scoped; per-worker cost/tokens unavailable.

Final promotion: Sol 6.1 Medium updated two bounded canonical test-hash references; lead owned sequential Git seals, integration and checks. No runtime/rule changes or repeated comprehensive review. No integration failure; per-worker tokens/cost unavailable.
