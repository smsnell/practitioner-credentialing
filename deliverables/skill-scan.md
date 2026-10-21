# G1 Skill-package check

The installed `scan-agent-skill` wrapper ran Cisco AI Skill Scanner **2.0.13**, local-only, with no cloud analyzer, uploads or API keys enabled.

## Disposition

- **CRITICAL — `credentialing/io.py:312`, COMMAND_INJECTION_OS_SYSTEM:** accepted as a scanner false positive after manual review. `_sealed()` already uses a fixed executable and an argument list, with no shell (`shell=False` by default). The formatted value is one literal `HEAD:<repository-relative-path>` argument to read-only `git cat-file -e`; shell syntax cannot execute. The path is derived beneath the selected repository output root. No source prose enters a shell command. The finding remains recorded; the scan is not represented as clean.
- **INFO — `SKILL.md`, missing license:** left for owner publication/licensing policy. No license was invented and nothing is being published at G1.
- **MEDIUM in the initial workspace scan — `requirements.txt:1`, unpinned dependency:** fixed by pinning the already-installed/tested jsonschema 4.19.2.
- **Two HIGH findings in the initial workspace scan — `.entire/metadata/01a10da8-6292-79c0-bdc5-ff8f9a404292/full.jsonl:1`:** historical capture text contains two shell installation examples. They are outside the runtime Skill package and are never read/executed by the processor. Capture records were preserved unchanged; no installation command was executed by this work.
- **Nine LOW hidden-file findings:** `.entire/logs/entire.log`; `.entire/metadata/01a10da8-6292-79c0-bdc5-ff8f9a404292/full.jsonl`; `.entire/metadata/01a15bc1-d044-7ae2-b190-81c4b18f30d3/{full.jsonl,prompt.txt}`; `.entire/settings.json`; `.entire/tmp/pre-prompt-01a15bc1-d044-7ae2-b190-81c4b18f30d3.json`; and `.entire/tmp/pre-task-{01a15c76-c8e8-76f1-9269-3193a94ffd70,01a15c77-274a-7463-ad44-35607513cd26,01a15c77-6628-7441-be23-47f3ab289790}.json`. These are existing session capture/configuration metadata, excluded from the source-only runtime package, not program inputs. No capture files were edited.
- **Two LOW bytecode findings:** `credentialing/__pycache__` and `tests/__pycache__`. Development caches are ignored in Git and excluded from the source-only package.

The full-workspace scan exited **1** with 16 findings. A source-only review copy under `/tmp/g1-skill-review` included all runtime Python, Skill/README, schema, requirements, tests, standing sources and original batch inputs, excluding Git/capture metadata and bytecode. The final package scan also exited **1**, with the CRITICAL false positive and INFO license item above. The report follows. Manual review checked entrypoint instructions, all runtime files, subprocess use, file writes and network/credential access: the CLI reads local inputs, writes only the chosen repository output directory, performs read-only Git sealing checks, and has no network/outreach/credential operations. Neither scan is certification or a claim of G1 acceptance.

## Final scanner output

# Agent Skill Security Scan Report

**Skill:** practitioner-credentialing
**Directory:** /tmp/g1-skill-review
**Status:** [FAIL] ISSUES FOUND
**Max Severity:** CRITICAL
**Scan Duration:** 1.17s
**Timestamp:** 2026-10-21T03:36:14.698659+00:00

## Summary

- **Total Findings:** 2
- **Critical:** 1
- **High:** 0
- **Medium:** 0
- **Low:** 0
- **Info:** 1

## Findings

### CRITICAL Severity

#### [CRITICAL] Shell command execution with string formatting (potential injection)

**Severity:** CRITICAL
**Category:** command_injection
**Rule ID:** COMMAND_INJECTION_OS_SYSTEM
**Location:** credentialing/io.py:312

**Description:** Pattern detected: subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"HEAD:{name}

**Code Snippet:**
```
result = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"HEAD:{name}"], capture_output=True)
```

**Remediation:** Use subprocess with argument lists, not shell strings. Never use user input in shell commands

### INFO Severity

#### [INFO] Skill does not specify a license

**Severity:** INFO
**Category:** policy_violation
**Rule ID:** MANIFEST_MISSING_LICENSE
**Location:** SKILL.md

**Description:** Skill manifest does not include a 'license' field. Specifying a license helps users understand usage terms.

**Remediation:** Add 'license' field to SKILL.md frontmatter (e.g., MIT, Apache-2.0)

## Analyzers

The following analyzers were used:

- static_analyzer
- bytecode
- pipeline


## Independent-review correction scan

After updating Skill outcome instructions and runtime evidence handling, ran the pinned local wrapper against `/tmp/g1-review-skill-nt6938qv` (source-only copy, excluding Git/capture metadata and caches). Exit **1**, scanner **2.0.13**, 2026-10-21T05:59:33 UTC: the same two findings, **CRITICAL** argv-formatting false positive at `credentialing/io.py:312` and **INFO** absent license in `SKILL.md`. Existing dispositions above still apply: fixed executable/list arguments with no shell; no licensing authority inferred. Changed modules parse local evidence and preserve source/authority boundaries; no new network, credentials or outbound actions. This is not a clean-scan claim or a comprehensive gate review.

## Q07 owner exception follow-up scan

After updating the Skill's outcome pointer and the small status mapping, the same local-only wrapper scanned the source-only package at `/tmp/g1-q07-skill-rv998w8d`, **2026-10-21 07:07:42 UTC**. Scanner **2.0.13**, exit **1**, two findings: **CRITICAL** `COMMAND_INJECTION_OS_SYSTEM` at `credentialing/io.py:312` (unchanged fixed executable/list argv, no shell; accepted false positive), and **INFO** missing license in `SKILL.md` (owner publication decision, no license invented). Manual inspection of this turn's changes found no added subprocess, network, credential, dispatch or human-decision operation. Existing dispositions above remain applicable; this is not a clean-scan or comprehensive gate-review claim.

## G2 continuation scan — before Batch-2 seal

Local pinned wrapper scanned `/tmp/g2-skill-xv8fhkvp` (runtime, tests, Skill/README/schema/dependency file, captured sources and B1/B2 inputs; excludes Git/capture metadata/caches), 2026-10-21 17:16 UTC, scanner **2.0.13**, exit **1**. Four findings: two **CRITICAL** argv-formatting patterns at `credentialing/continuation.py:19` and `credentialing/io.py:313`; **LOW** 124-file package; **INFO** absent license. Manual inspection accepts the two command-injection flags as false positives: fixed `git` executable, list argv, no shell, constrained repository-relative paths, read-only Git object inspection. File count reflects required original evidence and tests, not vendored dependencies; retain it. License remains an owner publication decision. No network/credentials/outreach or human judgment added by runtime. Not a clean scan or comprehensive gate review.
