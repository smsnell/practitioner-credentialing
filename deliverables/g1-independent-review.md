# Independent G1 review

Review date: 2026-10-21. Scope: independently assess the G1 blocker against the original requirements, complete snapshot schema, office sources linked in interview E-5, the interview itself, and representative batch records before evaluating the tracker and troubleshooting conclusions.

This document records the completed read-only review. Recommendations are proposals for owner review, not implemented changes or authorization to change the contract. No implementation, requirements, schema, source records, or working results were modified during the review. No credentialing run was executed.

## Conclusion

**G1 has a genuine contract gap, alongside implementation assumptions that should be corrected.** I could not find an existing status that truthfully represents the documented pre-dispatch hold. The missing-evidence holds are substantially justified, but they must describe facts **not established by the export**, rather than defects proved against all 40 applicants.

The smallest defensible resolution is an explicit contract clarification broadening the existing `intake-incomplete` description to cover the pre-dispatch phase. That would allow unresolved evidence and owned work to be represented without inventing dispatch, deadlines, verification, or approval. The implementation assumptions identified below require separate corrections; they do not explain away the current status gap.

## Evidence and review method

I read [REQUIREMENTS.md](../REQUIREMENTS.md), the complete [snapshot.schema.json](../snapshot.schema.json), [interview-E-5.md](../interviews/interview-E-5.md), all six linked office sources, and representative batch-1 records before evaluating the [project tracker](../PROJECT-TRACKER.md), [G1 troubleshooting report](g1-troubleshooting.md), [APP-001 evidence trace](g1-evidence-trace.md), and [Q07 compatibility report](g1-q07.md).

The six office sources were checked against their linked native Google Docs using the Google Drive skill and read-only connector calls:

| Local capture | Linked original |
| --- | --- |
| [Procedure](../sources/procedure.md) | [LARK-MSO-2026.1](https://docs.google.com/document/d/1v442U759TGLwnElS24xF1MmvovZjBSHy4KKe2Nl-GDk/edit) |
| [Accepted-source table](../sources/attester-table.md) | [LARK-ATT-2026.1](https://docs.google.com/document/d/1ze0RTP4H8J68FSqbFmkG7Qd_5cZiB6Lh2BfyU6v2Sj8/edit) |
| [Privilege criteria](../sources/privilege-criteria.md) | [LARK-PRIV-2026.1](https://docs.google.com/document/d/1auOI2S9mT7GRn3eS6HJv3wU5C9vDqGObfMmVF9Bc4fo/edit) |
| [Authority roster](../sources/authority-roster.md) | [LARK-AUTH-2026.1](https://docs.google.com/document/d/1Dvc3eJei4K7RyE8HZtZkMtRQNqE6VPQU8gUXVbps2xQ/edit) |
| [Export note](../sources/export-note.md) | [Office export note, 2026-03-16](https://docs.google.com/document/d/1UtQMnsCW78nPClsgEJV1DgBKlaiIkzNS-fT93-kTLgA/edit) |
| [Peer-reference form](../sources/peer-reference-form.md) | [LARK-REF-2026.1](https://docs.google.com/document/d/1p7lZMbDkrr34rqkv59OpGoZv_XBncpAz2WXCAH7Qa80/edit) |

All six captures matched the linked originals after line-ending normalization and trimming of boundary whitespace. Their local hashes also matched the source manifest. All 29 batch-1 files matched their capture hashes, and all 13 CSV tables matched the raw tables retained in working history. These comparisons establish capture/retention consistency; they do not prove that unexported documents do not exist in the office.

Representative records included APP-2026-001's application, history, verification replies and attempts, peer records, certification, correspondence, and committee recommendation; APP-2026-019's missing-items notice and intake data; APP-2026-018's return-incomplete notice and history; APP-2026-031's licence correspondence; and the written gap explanations for APP-2026-005 and APP-2026-039. Counts and retained-state comparisons were computed with independent standard-library scripts, without running the credentialing implementation.

## 1. Existing statuses do not truthfully cover the pre-dispatch intake hold

The [schema's status definition](../snapshot.schema.json) at line 162 rules out the plausible alternatives:

| Candidate | Why it does not fit |
| --- | --- |
| `intake-incomplete` | Requires an item already requested in writing and a running applicant clock. |
| `returned-incomplete` | Asserts that the file was returned. |
| `ineligible-clock-expired` | Requires an expired response clock. |
| `in-verification` | Requires a complete file. |
| `deferred` | Requires an admitted Governing Body deferral; it is not a generic waiting status. |
| `decision-inadmissible` | Does not cover files without refused decisions, and cannot bypass the schema's intake precedence. |
| Null, omission, or a new status | Violates the required status enumeration. |

The remaining statuses require readiness, approval, activation, denial, withdrawal, or discontinuation facts that do not establish a general pre-dispatch intake hold.

The interview explicitly requires holding the file and recording **pending dispatch**, with the response clock starting subsequently. It supplies no alternative status or permission to reinterpret the schema. See [E-5, Renata at 22:44](../interviews/interview-E-5.md), lines 880–884.

APP-2026-001 demonstrates the gap without depending on the implementation: its [application row](../inputs/batch-01/applications.csv), line 2, supplies release and CV receipt dates but no application-signature evidence; its only [indexed correspondence](../inputs/batch-01/correspondence.csv), line 10, is an inbound recommendation, not an applicant intake request.

**The exact contradiction:** every application must appear in the snapshot with a permitted status; required intake completeness is unestablished; no request, return, expiry or terminal event supports an intake status; and the interview forbids advancement or inventing dispatch. These obligations cannot all be satisfied under the unchanged status definition. An action-queue explanation cannot cancel a false status assertion. See [REQUIREMENTS.md, Snapshot contract](../REQUIREMENTS.md), lines 50–54, and the schema's required application fields and status definition, lines 139–178.

Substituting `intake-incomplete` would satisfy the mechanical enum check but contradict its stated meaning. The schema's intake-precedence sentence does not establish that dispatch occurred. Likewise, the broad business meaning of “Deferred” in the run outcomes does not broaden the narrower application-status enum.

## 2. Missing-evidence holds are mostly justified, with important distinctions

| Evidence requirement | Independent assessment |
| --- | --- |
| Application signature and date | **Outstanding for all 40 on the supplied evidence.** [Procedure §1](../sources/procedure.md), lines 20–22, separately requires application and release signatures. `release_signed_date` cannot establish both. This does not prove that any application was actually unsigned. |
| CV presence | **Established for 39; missing for APP-019.** Those 39 should not receive a missing-CV intake finding merely because the CV contents were not exported. The interview defines currentness through presence, without an additional age test. See [applications.csv](../inputs/batch-01/applications.csv) and [E-5, Renata at 20:50](../interviews/interview-E-5.md), line 750. |
| CV reconciliation | **Outstanding across the supplied batch.** Receipt dates cannot perform the required comparison with application and verified evidence. An unavailable CV also cannot establish a discrepancy. See [procedure §2](../sources/procedure.md), lines 35–45. |
| School and qualifying training accreditation | **Legitimate missing facts.** Accredited education and training are explicit criteria. APP-001's accepted registrar/GME replies verify its degree, specialty and dates, but do not establish accreditation. Its residency duration is already exactly 36 months. See [criteria](../sources/privilege-criteria.md), lines 6 and 15, and [APP-001 replies](../inputs/batch-01/verification-replies.csv), lines 2–3. |
| Direct peer return | **Outstanding provenance, distinct from eligibility.** The raw batch contains 57 peer replies, but their fields do not establish the return route. A request's portal method does not prove how the response arrived. The form explicitly excludes applicant-routed returns. See [reply fields](../inputs/batch-01/peer-reference-replies.csv), line 1; [APP-001 requests](../inputs/batch-01/verification-attempts.csv), lines 6–7; and [peer form](../sources/peer-reference-form.md), lines 3 and 46–53. Files without replies have a separate missing-response problem; the 57-row total is not a count of currently qualifying replies. |
| Referee addresses | **Not an export hold.** The export note expressly excludes this check and requires it to remain neither met nor failed. See [export exception](../sources/export-note.md), line 77. |

I considered the strongest contrary evidence: the [export note](../sources/export-note.md), line 74, says clean files are genuinely clean, and [APP-001's committee minute](../inputs/batch-01/decisions/2026-03-10_MEC-2026-011.md), line 19, says the file was presented. Neither identifies the missing facts. The later interview question expressly names signatures, CV reconciliation, accreditation and direct referee responses; Renata says missing required evidence remains outstanding. Treating the broad “clean files” statement as proof would override that specific answer. See [E-5, 21:33](../interviews/interview-E-5.md), lines 840–844.

An accepted source and an established fact are different questions. A registrar/GME reply can be admissible and establish the degree or training dates without establishing accreditation. Similarly, a peer reply can establish discipline, relationship, direct work and signature currency without establishing direct return. These established facts must remain retained; missing provenance is not proof of an inadmissible route, and missing accreditation evidence is not proof of an unaccredited programme.

The resulting eligibility questions also have explicit support: [criteria rule 6](../sources/privilege-criteria.md), line 79, requires referral while nothing yet verified supports a requested group, and permits withdrawal of the question when later verification establishes support. They are **not findings that all 40 applicants lack qualifications**, nor authority to discontinue them.

Independent counts and retained-output inspection confirmed:

- 40 applications and 41 application revisions.
- Release and CV receipt dates recorded for 39 current application revisions.
- Application-signature evidence listed as outstanding for all 40 current assessments; CV reconciliation also outstanding for all 40.
- 38 null working statuses and two supported intake statuses.
- Zero presentable packets in the retained results.

The two represented intake files are grounded in actual events. APP-019 has its documented March 20 deadline from the February 18 request for release and CV; APP-018 was actually returned incomplete and has an April 5 response deadline. See the [APP-019 letter](../inputs/batch-01/letters/2026-02-18_missing-items_APP-2026-019.md), line 8, and [APP-018 letter](../inputs/batch-01/letters/2026-03-06_return-incomplete_APP-2026-018.md), line 8. APP-019's existing letter does not establish that signature evidence or two named referees were also requested.

The APP-001 recommendation cannot supply missing underlying evidence or independently establish prior readiness. Refusing it for unestablished prior presentability remains defensible under [procedure §9](../sources/procedure.md), lines 194–200. A recommendation is not Governing Body approval.

## 3. Implementation assumptions exceeding the sources

### Missing evidence is hardcoded rather than assessed conditionally

Signature and CV-reconciliation holds are appended unconditionally; accreditation and peer provenance are always unverified. These conclusions fit the inspected evidence, but the code would not clear them merely because adequate evidence became available. That is a reusable-processing limitation, not proof that today's holds are wrong.

Code references:

- [engine.py](../credentialing/engine.py), lines 134–138: application-signature evidence is always appended to the missing list.
- [engine.py](../credentialing/engine.py), line 195: CV-reconciliation work is always appended.
- [evidence.py](../credentialing/evidence.py), lines 115–118 and 174–176: accreditation is initialized unverified and every education entry receives a missing-accreditation issue.
- [evidence.py](../credentialing/evidence.py), lines 259–265: every peer return receives missing-provenance and unusable results.

**Recommended correction:** make these evidence-dependent checks with traceable resolution when sufficient supplied evidence exists. Preserve today's holds until such evidence is actually available. The rules require facts to be established; they do not require permanent failure because a particular CSV lacks a dedicated column. This also follows the reusable Skill requirement in [REQUIREMENTS.md](../REQUIREMENTS.md), line 69.

### Changed entries automatically require a newly dated verification request

The code rejects earlier-request replies solely because their request predates the revision. The office instead requires reconciliation against existing verifications and entry-specific assessment of what changed. A fresh request may be necessary, but its date is not a universal admissibility condition.

References: [evidence.py](../credentialing/evidence.py), lines 127–145; [procedure §2](../sources/procedure.md), line 45; and the [usability rule](../sources/procedure.md), line 178. The latter explicitly says a later revision does not by itself void completed verifications and requires entry-by-entry evaluation.

**Recommended correction:** assess whether retained verification establishes the revised entry's relevant facts. Require fresh verification for facts not established, rather than using request date alone as a universal rejection rule. No current batch-1 assessment had this revision-mapping restriction applied, so it did not account for the batch-wide holds.

### Contact completeness is broader than specified

The code requires both contact name and email for every history entry. The intake rule requires a verification contact for employers and affiliations; it does not prescribe email or extend that intake condition to every school/training entry.

References: [engine.py](../credentialing/engine.py), lines 161–166, versus [procedure §1](../sources/procedure.md), line 28.

**Recommended correction:** scope the intake condition to the stated entry types and accept the contact information the authoritative rules actually require. Missing information needed to perform a particular verification can still generate owned verification work without inventing a broader intake rule. No current batch-1 hold arose from this overreach: the inspected entries all had both fields.

### “Partial” without a snapshot does not satisfy the contracted Partial outcome

The implementation deliberately emits `Partial` with no snapshot when statuses are unrepresentable. [REQUIREMENTS.md, Run outcomes](../REQUIREMENTS.md), lines 39–46, requires unsettled applications to remain in the snapshot. The current artifacts are useful diagnostic working results, but G1 remains blocked at snapshot production.

References: [io.py](../credentialing/io.py), lines 370–398, sets `Partial`, retains `snapshot: null`, and writes a snapshot only when no status is unrepresented. The [tracker](../PROJECT-TRACKER.md), lines 364–369, and [troubleshooting report](g1-troubleshooting.md), line 46, describe these working results as Partial while acknowledging the missing public snapshot.

**Recommended correction:** distinguish “diagnostic working results retained” from a contract-complete Partial batch result. Report G1's snapshot-production blocker explicitly; do not imply that retaining working files fulfills the required snapshot obligation. Evidence holds alone need not be run failures once they can be represented truthfully.

## Smallest defensible resolution for owner review

**One explicit contract clarification** would remove the representation blocker: broaden the existing `intake-incomplete` description to cover required intake completeness not yet established before dispatch. Proposed meaning:

> intake-incomplete — required intake completeness is not established. Before a written request is recorded, hold the file and queue MSP dispatch; no applicant response clock has started. After dispatch, apply the recorded request date and response deadline.

The existing action queue can carry the distinction, with `due: null` unless a record fixes a date. Existing documented requests retain their actual deadlines and coverage. No new enum or additional snapshot fields are necessary.

This changes the status's permitted meaning and therefore needs contract-owner review; it cannot be presented as an interpretation already authorized by the current wording. If the contract remains unchanged, no complete truthful batch-1 snapshot can be claimed from the inspected evidence. Substituting `in-verification`, a generic `deferred`, fabricated dispatch, or an invented status is not a defensible workaround.

After an authorized clarification, the proposed implementation correction is narrow: project the pre-dispatch hold using the clarified status while retaining the owned dispatch action, unknown deadline, evidence deficits, refusal history, and lack of approval/activation. Separately correct the evidence-handling and rule overreach identified above. Those corrections must not mark the present missing facts verified or manufacture readiness.

This agrees with the previous troubleshooting conclusion on the narrow Q07 incompatibility, but does not accept its implementation as free of unsupported assumptions. It also distinguishes the genuine missing-evidence problem from the snapshot-representation problem: obtaining every missing business fact is not necessary merely to represent unresolved work once the contract can express it.

## Limits and stop point

This review independently inspected batch-1 records and current working outputs; it did not process batches 2 or 3, rerun the credentialing CLI or test suite, or independently inspect the full IHS manual. Published-manual authority here is limited to quotations adopted in the supplied office sources. Local hash agreement is not an independent remote checksum for every batch file.

No files were modified during the original review, and no implementation was begun. This document is the sole file created by the subsequent instruction to save the review. All recommended contract and implementation changes remain unimplemented and await owner review.
