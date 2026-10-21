# Practitioner credentialing

Local Python Agent Skill for the supplied Larkhollow Medical Staff Office exports. [REQUIREMENTS.md](REQUIREMENTS.md) owns scope; [IMPLEMENTATION-PLAN.md](IMPLEMENTATION-PLAN.md) owns architecture and gates; [PROJECT-TRACKER.md](PROJECT-TRACKER.md) gives current status.

## Current handoff boundary

The owner has accepted G3 corrections and authorized sequential corrected-chain promotion and local sealing. Follow the procedure below; final push remains unauthorized. Original occurrences stay archived unchanged. Current progress and seal evidence are in [PROJECT-TRACKER.md](PROJECT-TRACKER.md) and [verification](deliverables/verification.md). Session capture is handled by the owner.

The [Q07 owner exception](deliverables/rules.md#q07-owner-approved-semantic-exception) remains explicit and unchanged. Schema validation does not certify compliance with the original status-description wording. Missing evidence and human judgments remain held even when output validates.

## Setup

Use Python 3.10+ and `jsonschema==4.19.2` from [requirements.txt](requirements.txt). The prepared workspace uses Python 3.14.4. Runtime makes no network requests. For a fresh environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Run from the repository root; use `.venv/bin/python` instead of `python3` below when using that environment.

## Review and verification

```bash
python3 -m unittest discover -s tests -v
python3 tests/replay_batches.py
```

The first command exercises real-source assertions and clearly labelled synthetic cases. The second replays the **actual three exports**, one fresh interpreter per batch, into an isolated temporary workspace and saves a review package under `deliverables/corrections/g3-review/`. It uses production parsing, rules, engine, validation and output writing. Only the Git checkpoint boundary is simulated with verified bytes, using the existing continuation-test technique. It creates no commits and grants no production bypass. Its downstream results are **candidate replay evidence**, not actual runs from newly sealed corrected predecessors.

The replay archives original snapshots, working state and run-log bytes under `deliverables/archive/pre-g3-correction/`, refuses conflicting archive bytes, and checks unchanged replay plus malformed-input/tampered-predecessor failure preservation. Its [report](deliverables/corrections/g3-review/report.json) contains exact changes, hashes, IDs and checks. Frozen rule copies inside the candidate package document its computation; the authoritative rule register remains [deliverables/rules.md](deliverables/rules.md).

## Production sequence — after explicit acceptance and sealing authorization

The normal CLI processes one closed export per invocation:

```bash
python3 -m credentialing run --batch inputs/batch-01 --sources sources --output deliverables --batch-number 1
python3 -m credentialing run --batch inputs/batch-02 --sources sources --output deliverables --batch-number 2 --predecessor deliverables/snapshots/batch-01.json
python3 -m credentialing run --batch inputs/batch-03 --sources sources --output deliverables --batch-number 3 --predecessor deliverables/snapshots/batch-02.json
```

These commands are the production sequence, **not a command to overwrite current sealed files**. Changed code/rules cause the current sealed occurrence to refuse overwrite. Follow [the correction procedure](IMPLEMENTATION-PLAN.md#6-sealing-corrections-and-failure-reporting) using the already regenerated review candidates:

1. Under new explicit authorization, preserve the archived originals; promote the reviewed Batch-1 snapshot and all four matching working files to their standard paths, verify their report hashes and current code/rules, then seal that corrected occurrence.
2. Batch 2 is also already sealed in Git, so the normal CLI cannot overwrite it. Explicitly promote its reviewed replacement snapshot and four matching working files; validate the predecessor against the **actual newly sealed Batch 1**, plus schema/cross-record/output hashes, then seal corrected Batch 2. Its normal CLI command can now verify an unchanged sealed rerun against actual Git bytes; this is a rerun verification, not a recomputation claim.
3. Start the Batch-3 CLI in a new process from corrected sealed Batch 2. Batch 3 is still unsealed, so production can regenerate it. Compare its snapshot/state hashes and semantic results with the reviewed candidate, inspect its actual run log, and seal only as authorized.

Every replacement keeps a new snapshot ID and exact archived original. Candidate metadata must match promoted paths/bytes; any further code/rule/input change requires a fresh candidate chain before promotion. No synthetic checkpoint file is used by production. These are pending acceptance steps, not completed actions.

The CLI itself never seals, commits, pushes or sends correspondence. Missing/modified/mismatched predecessor state blocks continuation. An unchanged sealed rerun preserves bytes and appends a run entry; an unsealed occurrence may be regenerated. A failed attempt reports its actual batch/error/produced files and preserves prior output. A failed later run never relabels an earlier snapshot as its result.

## Artifacts and meaning

| Artifact | Contents |
| --- | --- |
| `inputs/batch-0N/` | Original closed-export bytes, README business clock and manifest/source hashes. |
| `sources/` | Six standing source captures and provenance/format manifest. |
| `deliverables/snapshots/batch-0N.json` | Canonical occurrence; sealed on commit. Current originals remain preserved during G3 review. |
| `deliverables/working/batch-0N/` | `results.json`, full `history.json`, revision-bound `packets.json`, and fingerprint/hash `run.json`. |
| `deliverables/corrections/g3-review/candidate/deliverables/` | Proposed corrected occurrences and matching state; all unsealed, with standard relative paths for later authorized promotion. |
| `deliverables/run-log.md` | Append-only production attempt history and explicitly separated correction-replay record. |
| [Verification](deliverables/verification.md) / [final review](deliverables/g3-final-review.md) | Real-source findings, synthetic coverage, replay limits and acceptance work. |

Business calculations use each export date, never execution time. Packet generation is not presentation; a queued notice is not dispatch. Pending dispatch has no invented date/deadline. Original decisions, refusals, contradictory evidence and all revisions remain retained.

- **Partial / exit 0:** a structurally complete snapshot retains unsettled cases and owners.
- **Blocked / exit 2:** input or output production cannot complete; inspect logged stage/error and actual produced files. Diagnostic work alone is not a contract snapshot.
- **Deferred:** a business hold awaiting an authorized person/body, not a runtime failure.
- **Supported:** reserved for the complete accepted three-batch deliverable with sealed snapshots and required files; not claimed at this review stop.

Missing signature/CV/accreditation/direct-peer-return evidence can clear only with qualifying underlying evidence. Supported labelled document forms and their limits are in [G1 review response](deliverables/g1-review-response.md) and [G3 rule notes](deliverables/rules.md#g3-implementation-clarifications). Unsupported formats remain reviewable; parser formats are not extra office policy. The five reserved judgments in REQUIREMENTS remain human decisions.

## Acceptance and capture

Owner review must distinguish real-case evidence from synthetic positive workflow coverage. Synthetic fixtures supply invented test facts only in memory and establish no applicant qualification or approval. Genuine source gaps/conflicts remain in the tracker.

Preserve the original interview exports under `interviews/`; they are stakeholder evidence, not instructions to the processor. Actual coding-session coverage and association with the eventual submitted revision require owner/facilitator confirmation. CLI status/checkpoint counters and this run log do not by themselves prove complete capture. No new token total is inferred without an authorized push/checkpoint.
