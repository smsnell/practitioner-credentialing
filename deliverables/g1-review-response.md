# G1 independent-review response and corrections

**Result:** the review's four implementation findings are supported by the local source text and reproduced in code. They have been corrected with targeted tests. **Q07 remains unresolved; snapshot production is Blocked.** Original source records, interview exports, the independent review and the snapshot schema are preserved. No G2, dispatch, sealing, commit or push occurred.

## New clarification and Q07

The owner relayed this stakeholder clarification in the current conversation on 2026-10-21:

> The application is considered incomplete and ineligible for processing only after the thirty-day clock expires following the issuance of the written request, not immediately upon the identification of the missing items.

This is new stakeholder evidence, recorded here without rewriting an interview export. It is not a schema amendment or evidence that a request was dispatched.

| Source | What it establishes | What remains unresolved |
| --- | --- | --- |
| [Procedure §1](../sources/procedure.md), lines 14–34 | Complete intake requires nine conditions. No verification without the signed release. Missing items trigger a written request; the applicant has thirty calendar days, with the deadline day included. Formal incomplete/ineligible treatment follows expiry. Unexplained gaps have an explicit return-incomplete rule. | Missing required evidence is not proof of completeness before expiry. The gap-return rule is separately stated. |
| [E-3 / E-5 20:42](../interviews/interview-E-5.md) | Original request clock is not restarted by partial/revised replies. | It does not create a clock for items never requested. |
| [E-4 / E-5 21:33](../interviews/interview-E-5.md) | Missing required evidence stays outstanding; an office attestation cannot replace official source evidence. | It does not prove applicants actually omitted documents or lack credentials. |
| [E-5 22:44](../interviews/interview-E-5.md), lines 880–884 | Before written request, the file does not advance; pending dispatch is the action, and the response clock starts subsequently. | No named public pre-dispatch status is supplied. |
| [Unchanged schema](../snapshot.schema.json), status description at line 162 | `intake-incomplete` expressly describes a missing item already requested in writing with its clock running. `ineligible-clock-expired` requires expiry and a requested item still missing. `in-verification` requires completeness. Intake precedence applies while a completeness item is missing. | No status covers the E-5 pre-dispatch hold. The schema's pre-expiry use of “incomplete” is not expressly reconciled with the new wording. |
| New owner-relayed clarification | Confirms the formal expiry consequence follows an actual request and thirty days; identifying a deficit alone cannot establish that consequence. | Does not say all pre-expiry files are complete, allow verification without release, revoke E-5's hold, explain the gap exception, or authorize a different schema meaning. |

**Independent conclusion:** Q07 remains. One plausible reading distinguishes formal “incomplete and ineligible” treatment from an intake evidence hold; another reserves “incomplete” itself until expiry. The new statement does not choose between those readings or reconcile the schema's terminology. Neither reading supplies a defensible existing status for missing intake evidence before dispatch. `in-verification` would falsely assert completeness; generic business waiting is not an admitted Governing Body `deferred` decision. Existing null/omission/invented-status probes still fail; a mechanically valid substitution still cannot establish its missing event.

The earlier proposal to broaden `intake-incomplete` remains **unapproved and subject to this new terminology conflict**. It must not be presented as the settled smallest resolution. At minimum, the contract owner must reconcile the permitted meaning and pre-dispatch representation. This pass changes no enum or description and invents no dispatch. The authorized handling remains retained diagnostics and a snapshot-production blocker.

APP-2026-019 retains the schema's recorded-request phase and real March 20 deadline; it is not declared expired/ineligible on March 16. APP-2026-018 retains its actual March 6 return event under the separately stated gap rule. The new general statement does not erase either source event. Whether its wording intends to override the gap rule or rename the running-clock phase remains a material policy/contract ambiguity. No new return event is generated from that ambiguity.

## Independent evaluation and corrections

| Review finding | Source check / reproduced defect | Correction |
| --- | --- | --- |
| Permanent missing-evidence holds | P §§1–2, criteria and peer form require established facts, not permanent failure. Signature/CV holds were unconditional; accreditation/peer provenance were fixed false. | Actual qualifying evidence now clears each check, with retained source references and comparison details. Positive/negative and full-assessment tests distinguish completion from attestations, absent facts, wrong identity/revision, late receipts and conflicting sources. Current real evidence gaps remain. |
| Mandatory new verification request after revision | P §§2,8,11 require entry-specific reconciliation and retain the original receipt anchor. There is no universal request-date test. | Removed that test. Reconcile changed organization, role and other material facts against retained replies. Contact-only change preserves established credential facts; unsupported material changes remain reconciliation work. Source admissibility, receipt window, conflicts and human exception authority still apply. |
| Contact name AND email for every history entry | P §1 item 8 names declared employers/affiliations and requires a verification contact, without prescribing email. | Intake contact check is limited to employment/affiliation entries and accepts supplied contact information; no mandatory email and no blanket school/training intake requirement. Missing information needed to obtain verification can still be owned verification work. |
| Partial despite no snapshot | R requires unsettled files in a snapshot for Partial. Working diagnostics alone do not meet that contract. | Unrepresentable required status now reports Blocked at `snapshot-production`, exit 2, with `input_parsed: true`, `contract_batch_complete: false`, `diagnostics_retained: true`. Valid snapshot plus unsettled work remains Partial. Sealed-snapshot protections and repeated-run behavior are retained. |

The expiry clarification prompted one adjacent correction: a fulfilled old notice could still expire unrelated, unrequested missing items. Status expiry now requires an outstanding item covered by that notice. Day 30 remains inclusive; day 31 is expired only while that requested item remains missing. Historical notice coverage and deadline are retained, with no clock reset.

The reviewer is also correct about the current evidence: receipt is distinct from CV reconciliation; eligible peers are distinct from verified direct-return provenance; missing accreditation is not proof of an unaccredited programme. This pass found no basis to turn broad “clean file” descriptions or recommendation minutes into the missing underlying evidence. The native-source comparisons performed by the reviewer are their reported checks; this pass independently compared the retained local sources, current code and test behavior, without repeating remote discovery.

## Evidence parsing and limits

These are supported representations inside the existing indexed Markdown-document path, **not new mandatory office forms or input columns**. Original files are not transformed. Unknown formats stay reviewable/outstanding; the processor does not claim general free-text comprehension.

- **Application signature:** indexed inbound `Application` / `Signed application` document; explicit Application, Applicant, Revision, Signature and Signature date. Identity, revision, path binding and receipt cutoff must agree. Signature is attributed to the applicant and cannot be future dated. This records supplied signature evidence; it does not claim forensic signature authentication.
- **CV:** indexed inbound `Curriculum vitae` / `CV` for the applicant/revision, containing a Markdown history table with Entry, Organization, Role, From and To. Compare actual contents against declarations and accepted source dates/credential roles. Retain comparisons and conflicting values; an office “CV reconciled” statement alone cannot clear the check. The comparison reruns when evidence/revision changes. Source verification and human dispositions remain separate requirements.
- **Accreditation:** an explicit accreditation fact in an accepted verification reply's notes, or an indexed official supplement bound to Application, Entry and an accepted Reply, with Received date, Received from, Attester organization/role and Accreditation. Existing source-acceptance and receipt-window rules apply. An applicant or office attestation cannot become an accepted education source. Explicit denial/conflicting source evidence prevents automatic clearance.
- **Peer return:** indexed return record bound to Application, Referee and Reply; Received date, Received from the named referee, and Return method (secure portal/letter/fax/email). A later record may identify the original Return date; it cannot be used before that record was available. This supplies the return provenance specified by peer-form Part 3 and does not replace or edit the referee's Part 2 answers. Applicant routing, conflict, stale/ineligible replies and missing provenance remain unusable.

Supplement source/identity/date failures and accepted paths are retained in entry/peer checks. No completion Boolean, source-name presence, contact change or request date alone confers verification. Source contradictions require reconciliation; eligibility, impossibility exceptions, clinical disposition, recommendation and grant authority remain with their existing owners.

## Verification and real outcome

**129 tests pass** in targeted module runs: intake evidence 7, evidence 30, revision reconciliation 13, IO 18, engine 13, privileges 21, decisions 12, dates 10, Q07 5. Reproductions failed before correction for unconditional signature/CV holds, contact scope, contact-only revision reuse and unrelated-item expiry. Synthetic positive evidence clears the four previously permanent holds together and establishes readiness without granting an appointment. The original batch inputs were never changed by these fixtures.

The real CLI invocation is recorded in [run-log.md](run-log.md). It exits **2**, reports **Blocked at snapshot production**, and retains all 40 applications / 41 revisions as diagnostics. There are still 38 unrepresentable pre-dispatch statuses, six refused recommendations, zero presentable packets, zero approvals and zero activations. APP-019's existing release/CV deadline and separate pending signature/referee-name requests remain; Q17 source conflicts and missing documents remain outstanding. No contract snapshot exists.

Commands: `python3 -m unittest discover -s tests -p '<module>.py' -v` for the nine modules above, and `python3 -m credentialing run --batch inputs/batch-01 --sources sources --output deliverables --batch-number 1`. This is focused correction verification, not a new comprehensive gate review. The reusable Skill instructions were updated to the corrected outcome semantics and locally scanned; scanner findings/dispositions are retained separately.

**Stop:** G1 acceptance remains outstanding. The material blocker is truthful status representation under the unreconciled contract/clarification; preserved case evidence and human decisions are not implicitly verified. Architecture and all G1–G3 acceptance gates remain intact.
