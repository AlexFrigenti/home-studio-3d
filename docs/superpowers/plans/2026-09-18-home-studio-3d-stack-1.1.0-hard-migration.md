# Home Studio 3D Stack 1.1.0 Hard-Migration Implementation Plan

> **For agentic workers:** Read the companion design first. Execute only the explicitly authorized phase, stop at each human checkpoint, and do not infer authorization for the next phase.

**Goal:** Prepare and, only after separate authorization, hard-migrate Home Studio 3D from Stack 0.4.0 to the canonical Stack 1.1.0 snapshot.

**Architecture:** The migration remains a two-block MAJOR protocol. Block 1 constructs and verifies an inactive candidate and prepares project state; a human checkpoint separates it from Block 2, which activates the candidate under lock and validates Bootstrap, PSC, Preflight, session, and offline reentry. The public Stack release materializer is used only outside Git worktrees; Home never delegates candidate construction to `build:snapshot` alone.

**Tech Stack:** Git-commit-addressed Stack release materialization, Node/npm verification commands, Home manifest and Project Skill contracts, project lock, Bootstrap, PSC, Preflight, session/fallback validation, and the existing rollback primitive.

**Spec:** `docs/superpowers/plans/2026-09-18-home-studio-3d-stack-1.1.0-hard-migration-design.md`

## Global constraints

- Exact Stack authority: `83a2d7e244720a9e8cf716729ef141298838b0c8`.
- Exact Stack version: `1.1.0`.
- Expected candidate: 101 first-party, 99 dependencies, 200 payload, 202 tree, schema 2.
- Expected `snapshot.json` SHA-256: `6c2d4aecef0f6fee69b62a68cdfa245dec86ade7e095261fdd4ad4010e68b242`.
- Expected `checksums.json` SHA-256: `cb5cee99c807475cacfbc404abf6aa8d3d673d17ed0238856cb5f14ca074304c`.
- Home remains pinned and active at 0.4.0 throughout preparation.
- The materializer output is outside all Git worktrees and never directly targets Home.
- No automatic transition from preparation to activation.
- No synthetic native receipt, native-provenance overclaim, or offline-construction overclaim.
- Slice 007, Blender, MCP, machine bindings, and Plan 06 Block 4 remain out of scope.
- This draft does not authorize execution, staging, committing, or pushing.

## File and commit model

The final execution is expected to use two Home commits, with exact filenames and manifest details confirmed from evidence at execution time:

1. **Commit 1 — migration preparation:** inactive verified 1.1.0 candidate, approved Skill/frontmatter and preparation-only reconciliation. Pin and active remain 0.4.0.
2. **Commit 2 — activation/final migration:** coherent 1.1.0 activation, fresh Bootstrap/PSC/Preflight/session proof, and final migration evidence.

Do not fabricate commit SHAs in advance. The current task creates neither commit. Because `.ai-stack/state/**` is generated/untracked and not currently gitignored, both commit procedures must use explicit path manifests. Never use `git add .`, `git add -A`, or an equivalent broad staging command; generated PSC, Preflight, session, and disposable driver state must not be silently staged.

## PHASE 0 — authority and preflight

**Files:** none before execution.

- [ ] Verify Stack `main` is `83a2d7e244720a9e8cf716729ef141298838b0c8`, version 1.1.0, clean, synchronized, and unstaged.
- [ ] Verify Home is `feat/plan-06-ai-stack-pilot` at `1042e4246595cfa426a44060e082d4d8e94085fa`, clean and unstaged, with pin and active both 0.4.0.
- [ ] Confirm `.ai-stack/runtime/versions/1.1.0/` is absent before preparation and distinguish permitted generated `.ai-stack/state/**` from tracked work.
- [ ] Inspect `tests/plan_06/test_project_contract.py`; record that its 0.4.0 authority assertions remain the required preparation baseline.
- [ ] Confirm the six task IDs, current capability bindings, legacy Skill digest, and Slice 007 authority before changing anything.
- [ ] Stop for human decision if either authority, version, worktree, staging, or baseline contract differs.

## PHASE 1 — materialize the canonical candidate outside Git worktrees

**Files:** disposable output outside Stack, Home, and every Git worktree; no repository file is the materializer output.

- [ ] Create a fresh absent output path on a safe local filesystem.
- [ ] Pass repository-root and output-path values as safely quoted arguments; do not concatenate shell command strings, especially when paths contain spaces.
- [ ] Run the public Stack command with exact commit and version:

```text
npm run materialize:release-snapshot -- --commit 83a2d7e244720a9e8cf716729ef141298838b0c8 --version 1.1.0 --output "<fresh-output>" --json
```

- [ ] Capture bounded evidence only; do not pass dependency roots or release-internal arguments.
- [ ] Stop if the command does not report a verified, reproducible candidate or if it writes anywhere other than the requested disposable output and its owned temporary workspace.

## PHASE 2 — verify candidate identities and closure

**Files:** disposable candidate only.

- [ ] Run the supported standalone verifier against the disposable output:

```text
npm run verify:snapshot -- "<fresh-output>"
```

- [ ] Verify schema 2, counts 101/99/200/202, and the two canonical SHA-256 identities from the design.
- [ ] Confirm the dependency-complete closure, including `ajv@8.20.0`, `ajv-formats@3.0.1`, `fast-deep-equal@3.1.3`, `fast-uri@3.1.7`, and `json-schema-traverse@1.0.0`; confirm unreachable `require-from-string` is not silently included when the canonical closure excludes it.
- [ ] Prove the retained candidate is runtime-offline autonomous according to existing offline verification semantics. Do not claim its construction was offline.
- [ ] Stop and delete the disposable candidate if any identity, closure, schema, or verification result differs.

## PHASE 3 — controlled inactive copy/staging into Home

**Files:** `.ai-stack/runtime/versions/1.1.0/` and only the Home paths approved by the existing migration contract. This phase uses a controlled filesystem copy, not a Stack installation primitive.

- [ ] Confirm the candidate remains outside Git worktrees while verification completes.
- [ ] Confirm `.ai-stack/runtime/versions/1.1.0/` does not exist. If it exists unexpectedly, stop; do not overwrite, merge, or reuse it.
- [ ] Copy the already verified external candidate into `.ai-stack/runtime/versions/1.1.0/` using a controlled filesystem operation. Do not call `installSnapshot` and do not call `sync:snapshot`; Stack `installSnapshot` activates and `sync:snapshot` correctly rejects this MAJOR transition.
- [ ] Do not modify `.ai-stack/checksums.json` and do not edit `.ai-stack/manifest.json` in this phase.
- [ ] Verify the Home candidate’s files and hashes against the disposable verified candidate.
- [ ] Re-read the installed inactive snapshot identity and require `.ai-stack/runtime/versions/1.1.0/` to verify.
- [ ] Explicitly re-read active authority and require `active = 0.4.0`; explicitly re-read manifest authority and require `pin = 0.4.0`.
- [ ] No active-checksums mutation, manifest-pin mutation, Bootstrap under 1.1.0, PSC generation under 1.1.0, Preflight, session, Blender, or MCP action is allowed in this phase.
- [ ] Stop on any partial copy, unexpected tracked path, pin/active change, or candidate verification failure.

## PHASE 4 — migrate Project Skill frontmatter

**Files:** the existing Home Project Skill only, during separately authorized migration execution.

- [ ] Prepend the approved canonical frontmatter to the current Skill, which has no frontmatter:

```yaml
---
name: home-studio-3d
description: Home Studio 3D project guidance for canonical context and task routing.
---
```

- [ ] Preserve the existing legacy Skill body byte-for-byte after the frontmatter prefix; do not add an unspecified extra blank line.
- [ ] Verify the legacy body digest before the operation, the complete migrated digest `0fdb73131da8875ebe2fd5144da874d2a77f46edd7cf736684dc4a477c6e5ea1` after it, and exact body-byte equality.
- [ ] Do not start a Stack 1.1.0 session or treat the Skill as activation authority during preparation.

## PHASE 5 — preparation-only Home reconciliation

**Files:** Home manifest/tests/docs required by the approved preparation scope, confirmed from execution-time evidence.

- [ ] Reconcile only the target-specific manifest/tests/docs required to describe the inactive 1.1.0 candidate and the preparation state.
- [ ] Leave `tests/plan_06/test_project_contract.py` unchanged in Commit 1; its 0.4.0 expectations must remain green while the candidate is inactive.
- [ ] Preserve the six task IDs and existing capability architecture; add no task DSL and no machine bindings.
- [ ] Keep manifest pin 0.4.0 and active snapshot 0.4.0. Do not update the active pointer or activate the candidate.
- [ ] Keep Slice 007 authority unchanged and perform no Blender regeneration, MCP operation, protected promotion, or Slice 008 work.
- [ ] Review the diff for stale normative 1.0.0 instructions, direct use of `build:snapshot`, direct materializer output into Home, stale PSC authority, synthetic native claims, or automatic Plan 06 continuation.

## PHASE 6 — preparation verification

**Files:** the candidate and preparation-only Home changes.

- [ ] Verify candidate and checksums again from Home’s inactive location.
- [ ] Verify manifest pin/active coherence remains 0.4.0 and no project authority has transitioned.
- [ ] Run the unchanged `tests/plan_06/test_project_contract.py` and require the 0.4.0 authority assertions to remain green.
- [ ] Verify Skill bytes/digest, task IDs, capabilities, and preparation docs.
- [ ] Run the repository-approved read-only migration/preparation checks; do not invoke Bootstrap, PSC creation, Preflight, session start, or offline reentry before activation.
- [ ] Run `git diff --check` and inspect the complete preparation diff.
- [ ] Stop if a blocker or major finding remains.

## PHASE 7 — preparation commit, only after authorization

**Files:** exact preparation manifest determined in Phases 3–6.

- [ ] Stage only the approved preparation paths with explicit filenames.
- [ ] Confirm the staged diff contains no activation, machine-binding, generated receipt, Slice 007, or unrelated changes.
- [ ] Stage only explicit preparation paths; do not stage `.ai-stack/state/**`, generated PSC/Preflight/session state, or any disposable materializer/driver workspace.
- [ ] Create Commit 1 using the repository’s approved migration message convention.
- [ ] Reverify the committed preparation state and keep pin/active at 0.4.0.

## PHASE 8 — HUMAN CHECKPOINT

Stop completely and return:

```text
HOME STACK 1.1.0 MIGRATION PREPARATION VERIFIED — READY FOR ACTIVATION AUTHORIZATION
```

No later phase begins automatically. Activation requires separate explicit human authorization.

## PHASE 9 — activation under project lock (not authorized by this draft task)

**Files:** a disposable one-shot migration driver plus Home runtime authority and active checksums; the project-owned manifest edit is the separate controlled operation in Phase 10. The driver is execution scaffolding, not a new public Stack API, and must not be silently tracked.

- [ ] Before writing the driver, inspect the installed exact Stack 1.1.0 payload and verify the actual module path, `installSnapshot` export, arguments/signature, `withProjectLock` behavior, lock-token semantics, and candidate/source expectations. If any assumption differs, stop.
- [ ] Import `installSnapshot` and `withProjectLock` from the verified project-local Stack 1.1.0 snapshot/runtime, not from the central Stack checkout.
- [ ] Operate on the explicit Home project root and consume the already verified inactive 1.1.0 candidate.
- [ ] Acquire the existing `withProjectLock` primitive or canonical equivalent once for the entire authority transition.
- [ ] Reverify the 0.4.0 baseline and inactive 1.1.0 candidate under the lock.
- [ ] Use the existing verified `installSnapshot` primitive with the held lock token where the actual API supports it; do not implement a new MAJOR migration command.
- [ ] Do not call `sync:snapshot`; its correct result for this transition is `major-migration-required`.
- [ ] Activate the verified 1.1.0 snapshot/checksums and verify `active = 1.1.0` before editing the manifest.
- [ ] Treat any transient active=1.1.0/pin=0.4.0 state as fail-closed, never as a usable state.

## PHASE 10 — explicit manifest edit and coherence

- [ ] While the same authority-transition lock remains held, explicitly edit the project-owned `.ai-stack/manifest.json`, changing only `stackVersion` from 0.4.0 to 1.1.0. There is no canonical Stack manifest-write callable.
- [ ] Inspect the exact manifest diff; do not change tasks, capabilities, context, Skill path, or unrelated fields.
- [ ] Verify pin, active snapshot, installed version, checksums, and manifest are coherent.
- [ ] Release the authority-transition lock only after pin and active are both verified as 1.1.0.
- [ ] Roll back through the approved primitive if coherence cannot be established.

## PHASE 11 — fresh Bootstrap and PSC

- [ ] Run fresh Bootstrap under the coherently activated Stack 1.1.0.
- [ ] Generate a fresh PSC and verify it against current Stack/Project Skill authority.
- [ ] Do not treat a stale or failed PSC as authority.

## PHASE 12 — Preflight

- [ ] Run Preflight for the first post-migration task `project-documentation-read`.
- [ ] Require non-blocked results and current Skill, PSC, manifest, snapshot, and capability evidence.
- [ ] Do not perform Blender or MCP work for this validation.

## PHASE 13 — session validation

- [ ] Validate a session with genuine supported native evidence if available.
- [ ] If native evidence is unavailable, state that limitation explicitly and use the verified Canonical Handoff fallback only after Bootstrap, PSC, Preflight, exact Skill bytes/digest, and bindings are proven current.
- [ ] Classify a proven fallback as `READY-WITH-WARNINGS`; classify an unproven fallback as `BLOCKED`.
- [ ] Never use structural/synthetic receipts as native provider attestation.

## PHASE 14 — offline reentry proof

- [ ] Prove runtime operation from Home, the project-local verified 1.1.0 snapshot, and permitted machine-owned capabilities with the central Stack checkout, GitHub, Internet, external `NODE_PATH`, and host `node_modules` unavailable.
- [ ] Do not confuse this runtime proof with offline candidate construction.

## PHASE 15 — final verification and activation commit

**Files:** exact activation/final migration paths determined by the approved runtime primitives.

- [ ] Verify active 1.1.0, manifest pin 1.1.0, checksums, Bootstrap, PSC, Preflight, session/fallback evidence, and offline reentry.
- [ ] Verify Slice 007 remains unchanged and no protected promotion occurred.
- [ ] If any activation/session validation fails, restore verified coherent 0.4.0 authority using the approved rollback primitive and report the failure.
- [ ] If the manifest pin advanced, explicitly restore `.ai-stack/manifest.json` to `stackVersion: 0.4.0`; do not imply that the rollback primitive edits the manifest.
- [ ] Verify `active = 0.4.0`, `pin = 0.4.0`, and the restored active snapshot under the appropriate project lock. Do not treat a failed/new PSC as authority.
- [ ] Create Commit 2 only after all final checks pass; do not fabricate its SHA in advance.

## PHASE 16 — final human acceptance

Stop and return:

```text
HOME STACK 1.1.0 MIGRATION COMPLETE — HUMAN ACCEPTANCE REQUIRED BEFORE PLAN 06 RESUMPTION
```

Plan 06 productive work and Block 4 remain paused until explicit human acceptance.

## Execution-time API rule

Before Phases 3, 7, 9, or 15, inspect canonical Stack and Home code to confirm the exact callable names and signatures for `withProjectLock`, verified snapshot installation/activation, Bootstrap, Preflight, session/fallback validation, and rollback. Inspect the project-owned manifest edit separately; it is not a Stack callable. The one-shot driver must be disposable unless execution-time evidence separately authorizes tracking. This plan intentionally references the existing approved primitives semantically rather than inventing a new public API.

## Historical gap record

P06-MIG-GAP-001 occurred because `build:snapshot` alone produced 101 first-party, 0 dependency, 101 payload, and 103 tree entries instead of the canonical 101/99/200/202 dependency-complete release snapshot. The failed candidate was rejected and deleted. No Home migration occurred. The supported `materialize:release-snapshot` path is now the required construction mechanism for Stack 1.1.0.

## Stop conditions and exclusions

Stop for human review on authority drift, unexpected dependency or payload changes, any identity mismatch, unsafe output path, partial candidate, pin/active transition during preparation, stale PSC use, unproven fallback, offline-proof overclaim, Slice 007 mutation, or any blocker/major review finding.

This documentation draft authorizes no Home mutation, no manifest or Skill edit, no candidate installation, no activation, no Bootstrap, no PSC, no Preflight, no session, no machine-binding change, no Blender/MCP operation, no protected promotion, no offline-reentry execution, no commit, no push, and no Plan 06 Block 4 resumption.
