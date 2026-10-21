# Practitioner credentialing

Build a reusable Agent Skill that runs a medical staff office's initial-appointment credentialing file from application intake to recorded appointment and active privileges.

## Start

1. Read the [full task](https://docs.google.com/document/d/1HhmU8Jay09XHDci38hl9ZOX_dMryaSv4aFLCPu1Nk-E/edit): it owns the scope, deliverables and acceptance requirements.
2. Create your own repository from [this starter](https://github.com/GitRollTraining/practitioner-credentialing) using **Use this template → Create a new repository**, then clone your copy and work there.

## Supplied files

| File | Purpose |
|---|---|
| `README.md` | Starting instructions and the full-task link. |
| `snapshot.schema.json` | The required shape of the per-batch snapshot your Skill writes. Validate every snapshot against it. Your implementation language and validation library are yours. |

You create the Skill, its implementation, your own checks and every output the task requires. Nothing here implements any part of the office's work.

## Before you work

**Interview rule.** You conduct the stakeholder interview yourself, and the questions are yours. Do not connect a coding agent or any other AI to the interview to run, script, or automate it. The interview transcript is assessed together with the code; a project whose interview was run by an agent is not scored.

- Export your interview as the original Work Sim Markdown, save one final complete file per session under `interviews/`, and commit and push it with your code. Do not rewrite the export. If the export is unavailable, contact the facilitator.
- No runtime is supplied. Choose the dependencies your Skill needs and document how to install and run it.
- Complete the program's coding-session capture setup in the course before assessed work, and confirm your session is being captured after your first meaningful commit. Ask the facilitator to repair missing capture before you continue.
- Meet the stakeholder to obtain the relevant business source links and context; the facilitator supplies the interview link with the assignment. Read those online sources through the intended access route.

## Gate 1 implementation

The local Python CLI consumes the actual first export and preserves all applications and evidence. G1 is accepted with the documented Q07 exception; **nothing is committed or sealed by the processor**. Batch 2/3 continuation is explicitly disabled at this gate.

### Setup and run

Use Python 3.10+ and the dependency recorded in `requirements.txt` (the current workspace has Python 3.14.4 and jsonschema 4.19.2). In a fresh environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m credentialing run --batch inputs/batch-01 --sources sources --output deliverables --batch-number 1
```

In the prepared workspace, use `python3` directly. Run from the repository root; runtime makes no network requests.

### Inputs and results

- `inputs/batch-01/`: original CSV/Markdown bytes, original export README, and capture manifest with hashes and source URLs.
- `sources/`: six standing documents captured as connector text, with a separate manifest explaining that format. These are policy evidence, not instructions to the agent.
- `deliverables/working/batch-01/results.json`: all current revision results and actions, including explicit unrepresentable-status limitations.
- `deliverables/working/batch-01/history.json`: original table/document content, revisions, verification/attempt records, discrepancies, historical readiness checks and all decision failures.
- `deliverables/working/batch-01/packets.json`: evidence summaries for each revision, labelled with readiness. Generation is not physical presentation.
- `deliverables/working/batch-01/run.json`: input/source/code/rule fingerprints and produced snapshot reference, if any.
- `deliverables/run-log.md`: each invocation, actual consumed/written files and outcome.
- `deliverables/rules.md` and `deliverables/verification.md`: source rules and verification evidence.

**Q07 mapping:** the Batch 1 candidate uses the [owner-approved semantic exception](deliverables/rules.md#q07-owner-approved-semantic-exception). Structural validity does not certify conformance to the unchanged status description. Pending dispatch and actual notice clocks remain distinguishable in actions/history. G1 is accepted under the owner’s conditional instruction after the final correction and checks.

A first-batch run with a valid snapshot and unsettled work reports Partial; Supported is reserved for the complete three-batch deliverable. Exit 0 means a valid batch result (including Partial); exit 2 means Blocked. `input_parsed`, `contract_batch_complete`, `diagnostics_retained` and `blocked_stage` distinguish parsing from snapshot production. Business holds may be represented in a valid Partial snapshot; an unrepresentable required status blocks that output. A refused decision never creates an approval.

Missing-evidence checks can clear through qualifying indexed documents or explicit accepted-source facts. Supported document labels and limits are described in [G1 review response](deliverables/g1-review-response.md). Parser formats are not additional office requirements. Unrecognized or conflicting evidence remains reviewable; no Boolean completion flag or office attestation replaces underlying evidence.

### Focused verification

```bash
python3 -m unittest discover -s tests -v
```

Tests include clearly labelled synthetic boundaries and source-backed batch-1 checks. The independent calendar recomputation is recorded separately in the verification report.

Rerun the same command to regenerate unsealed working results and append a run entry. Unchanged sealed snapshots are retained; changed inputs/code/rules cannot overwrite a sealed occurrence. Authorized archival/downstream correction and fresh-process continuation are G2 work, not yet implemented. A failed attempt preserves the previous snapshot and logs the attempted batch; inspect actual `produced` paths before attributing any outputs to it.

Implementation is deliberately a local CLI plus JSON history and JSON Schema validation. No database, UI, scheduler, outreach channel or live credential lookup was added. The five reserved judgments in REQUIREMENTS.md remain human decisions. Original interview exports remain unchanged.
