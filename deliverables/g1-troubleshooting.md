# G1 focused troubleshooting

Historical troubleshooting checkpoint. The subsequent [independent-review response](g1-review-response.md) corrects additional implementation assumptions and the earlier “Partial without snapshot” outcome terminology. Current snapshot production is Blocked; the original run log is retained.

**Result:** two misleading action/explanation paths corrected; G1 acceptance remains outstanding under Q07. Architecture, business rules, source records and gate criteria are unchanged. No G2, dispatch, commit, seal or push occurred.

## Representative evidence trace

[APP-2026-001 trace](g1-evidence-trace.md) follows original rows, governing source clauses and retained checks. School/residency accreditation, direct peer-return provenance, application signature/date evidence and actual CV contents for reconciliation are genuinely absent from the export. This is not evidence that the practitioner lacks those credentials or that the office never received the documents. Release and CV receipt, degree/residency dates, active certification and eligible peer replies are present and retained. All 13 CSV tables match retained raw tables, and all 29 captured input files match their manifest hashes. No ingestion loss was found in this trace.

An unsupported case-specific explanation was corrected: VR-0101 covers 2010-07-01–2013-06-30, exactly 36 full calendar months. Missing accreditation does not create a partial-month arithmetic ambiguity. `privileges.duration_note` now adds Q04 only for a matching completed interval that actually needs partial-month arithmetic. Accreditation remains outstanding; neither privilege support nor readiness was fabricated. The source-backed regression failed before the fix and passed afterward; the genuine partial-month CARD fixture still passes.

## APP-2026-019: existing notice versus new work

Source: [February 18 letter](../inputs/batch-01/letters/2026-02-18_missing-items_APP-2026-019.md), indexed as LTR-0004 in [correspondence.csv](../inputs/batch-01/correspondence.csv). Its two requests are the signed/dated Larkhollow release and a current CV. Its deadline is **2026-03-20**, thirty calendar days after dispatch. At the March 16 export, that clock is running. [Application row](../inputs/batch-01/applications.csv) has blank release/CV dates; [peer-referees.csv](../inputs/batch-01/peer-referees.csv) has no APP-2026-019 rows. Application signature/date evidence is absent from the export. B02/B40 require those missing facts to remain outstanding; B03 preserves the existing clock; B44 forbids inventing a new one.

| Queue work | Owner | Due / event treatment |
| --- | --- | --- |
| Await signed and dated release | Applicant | Existing March 20 deadline; letter path retained |
| Await current CV | Applicant | Existing March 20 deadline; letter path retained |
| Pending written request for application signature/date evidence and two named referees | MSP | Null; neither item appears in the existing letter; no new dispatch inferred |
| Obtain admissible source verification | MSP | Explicitly held until signed release; no invented request/date |
| Obtain actual CV and reconcile it | MSP | Outstanding separate comparison work; recorded notice does not prove CV receipt/reconciliation |

**Cause:** intake generated generic requests independently of notice contents, then a keyword-based release hold incorrectly caught intake requests. An extra queue item presented retained notice history as new work. Some verification actions said “obtain admissible verification” and escaped the keyword hold.

**Correction:** recognized notice templates retain explicit requested items; pending requests name only uncovered requirements. Existing covered items carry the original deadline. Notice history stays in retained intake history, without a redundant historical queue action. Release holds apply to verification elements and include “obtain admissible” wording; intake correspondence remains possible. An unrecognized notice scope queues MSP review before any additional dispatch is inferred. A notice naming one gap cannot establish coverage of other unexplained intervals. This is bounded parsing of supplied formats, not a claim to understand arbitrary correspondence.

The actual APP-2026-019 regression first failed because the existing items had no attributed deadline. It now checks both existing actions, both new missing items, no duplicate release request, no clock reset, and held verification outreach. Synthetic missing-notice/unrecognized-wording probes check that no extra clock or dispatch is manufactured. Status remains `intake-incomplete`; no case evidence was added.

## Exact contract incompatibility

[Q07 proof](g1-q07.md) isolates the unchanged schema's application definition against APP-2026-001. Null status fails the enum, omission fails required, and invented `pending-dispatch` fails the enum. Substituting `intake-incomplete` passes mechanical validation but conflicts with its recorded-request/running-clock description. The current authorized handling is retained working holds with no public snapshot. The smallest proposed semantic contract change is broadening that existing status description to include pre-dispatch holds; explicit contract-owner authorization is still required. No schema permission is inferred from permission to develop known logic.

## Focused checks and refreshed output

Commands run individually:

```bash
python3 -m unittest discover -s tests -p test_engine.py -v
python3 -m unittest discover -s tests -p test_privileges.py -v
python3 -m unittest discover -s tests -p test_evidence.py -v
python3 -m unittest discover -s tests -p test_dates.py -v
python3 -m unittest discover -s tests -p test_q07.py -v
python3 -m credentialing run --batch inputs/batch-01 --sources sources --output deliverables --batch-number 1
```

**64 focused tests pass:** engine 13, privileges 21, evidence 15, dates 10, Q07 5. These include eight added tests across engine/Q07; the prior full G1 suite passed 85 tests. No comprehensive gate review was repeated. Batch-1 working results/history/packets were refreshed through the CLI; each of the three troubleshooting invocations remains in [run-log.md](run-log.md). Latest outcome remains Partial: 40 applications / 41 revisions, 38 null status limitations, six refused recommendations, zero ready packets/approvals/activations. No public snapshot exists. No original interview, input, standing-source or schema change was needed.

## Remaining acceptance blockers

Q07 still prevents a complete truthful G1 snapshot under unchanged S. Owner acceptance remains pending. Required missing case evidence and Q17 source conflicts remain owned casework, not implicit passes or reasons to reopen discovery. Later-batch state continuation and final capture/handoff checks remain at their original gates. The proposed contract disposition is a recommendation for review, not executed authority.
