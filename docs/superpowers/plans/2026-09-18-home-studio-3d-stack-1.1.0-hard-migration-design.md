# Home Studio 3D Stack 1.1.0 Hard-Migration Design

**Status:** Documentation draft for human review. This document authorizes no migration activity.

## Provenance and reconciliation

The migration architecture was designed and human-approved during Plan 06. The original conversational target was Stack 1.0.0, but the previously referenced 1.0.0 design and implementation-plan paths were never materialized and do not exist in Home Git history. This document is a new canonical draft; it is not a restoration of a historical file and does not claim historical Git provenance.

P06-MIG-GAP-001 exposed that `build:snapshot` alone produced a first-party-only candidate (`101 / 0 / 101 / 103`) rather than the dependency-complete release candidate (`101 / 99 / 200 / 202`). The failed candidate was rejected and deleted; no Home migration occurred. Stack 1.1.0 introduced the canonical public dependency-complete release materializer. After Stack 1.1.0 became canonical, the human explicitly selected migration path B: Home 0.4.0 → Stack 1.1.0.

The approved R1 reconciliation changes target authority, candidate-construction tooling, identities, and corresponding wording. It does not redesign the approved hard-migration architecture, its checkpoints, or its rollback semantics.

**Reconciliation classification: R1 — TARGET-ONLY DOCUMENT RECONCILIATION.** Stack 1.1.0 changes the released authority and the supported way to construct the dependency-complete candidate, but the Home migration remains the same explicit preparation/checkpoint/activation protocol.

## Goal and terminal state

Migrate Home Studio 3D from Stack 0.4.0 to Stack 1.1.0 through an explicit MAJOR hard-migration protocol.

A successful terminal state has all of the following properties:

- the manifest declares `stackVersion: 1.1.0`;
- the active snapshot is 1.1.0;
- `.ai-stack/runtime/versions/1.1.0/` is installed and verified;
- a fresh valid PSC is generated under Stack 1.1.0;
- Preflight is non-blocked for `project-documentation-read`;
- session context is validated through genuine supported native evidence, or through the verified Canonical Handoff fallback when native evidence is unavailable;
- offline reentry is proven;
- Slice 007 authority is unchanged.

## Canonical authorities and identities

The Stack authority for this migration is:

```text
STACK_1_1_0_MAIN_AUTHORITY=83a2d7e244720a9e8cf716729ef141298838b0c8
version=1.1.0
snapshot.json sha256=6c2d4aecef0f6fee69b62a68cdfa245dec86ade7e095261fdd4ad4010e68b242
checksums.json sha256=cb5cee99c807475cacfbc404abf6aa8d3d673d17ed0238856cb5f14ca074304c
first-party=101
dependencies=99
payload=200
tree=202
schema=2
```

These identities are release evidence, not values to be regenerated or rewritten by Home. The candidate must be constructed from the exact Stack authority and verified before it is copied into Home.

Home begins at the recorded baseline:

```text
HEAD=1042e4246595cfa426a44060e082d4d8e94085fa
pin=0.4.0
active=0.4.0
```

The design does not claim that Stack 1.0.0 was ever installed in Home.

## MAJOR hard-migration invariants

Ordinary PATCH/MINOR synchronization is not sufficient across 0.4.0 → 1.1.0. The migration requires explicit human authorization and is divided into two blocks:

1. **BLOCK 1 — PREPARATION:** construct, verify, and stage an inactive 1.1.0 candidate and prepare the approved project documentation changes.
2. **HUMAN CHECKPOINT:** preparation must be reviewed and explicitly accepted.
3. **BLOCK 2 — ACTIVATION + SESSION VALIDATION:** only after new authorization, activate 1.1.0 under the project lock and validate the resulting project session.

Preparation must never transition automatically into activation. During preparation, Home remains pinned to and active on 0.4.0. A transient pin/active mismatch is fail-closed and is not a usable project state. The existing PSC is historical/generated state and cannot authorize Stack 1.1.0.

Activation must preserve candidate verification, project locking, coherent authority transition, fresh Bootstrap, fresh PSC, fresh Preflight, session validation, explicit fallback semantics, and rollback. No silent promotion is permitted.

## Canonical candidate construction

The only approved preparation path is:

```text
exact Stack authority 83a2d7e244720a9e8cf716729ef141298838b0c8
  → npm run materialize:release-snapshot -- --commit <SHA> --version 1.1.0 --output "<fresh-output>" --json
  → fresh output outside every Git worktree
  → dependency-complete verified candidate
  → npm run verify:snapshot -- <fresh-output>
  → confirm the canonical identities and 101/99/200/202/schema-2 evidence
  → controlled inactive copy/stage into Home
```

The public materializer must not write directly into the Home worktree. Its output is disposable until independently verified. `build:snapshot` alone is explicitly rejected: it is a first-party-only builder and does not establish the required dependency-complete release candidate.

`materialize:release-snapshot` is Stack 1.1.0 build-time tooling. It is not part of `runtime/snapshot-files.json` and is not required inside the installed Home runtime. Its role ends after constructing and proving the exact candidate that is then copied into Home by the migration protocol.

Block 1 performs inactive staging with a controlled filesystem copy only. It must not call `installSnapshot` or `sync:snapshot`, and it must not modify `.ai-stack/checksums.json` or `.ai-stack/manifest.json`. If `.ai-stack/runtime/versions/1.1.0/` already exists unexpectedly, preparation stops rather than overwriting or merging it. After the copy, verify the installed inactive tree and hashes against the external candidate, then re-read and require `active = 0.4.0` and manifest `pin = 0.4.0`.

All repository-root and output-path placeholders must be passed as safely quoted path arguments, including paths containing spaces. The materializer must receive the explicit Stack commit, version, and disposable output path without shell-string interpolation.

## Preparation state

After Block 1, Home may contain `.ai-stack/runtime/versions/1.1.0/` as an inactive verified project-local candidate. The Project Skill may be migrated and preparation-only tests/docs may be reconciled. Until activation is separately authorized, all project authority remains:

```text
manifest pin=0.4.0
active snapshot=0.4.0
```

No Stack 1.1.0 Bootstrap, session, or task execution occurs before activation. The old PSC is not reused as 1.1.0 authority.

## Project Skill

The current legacy Skill digest is:

```text
54da6d774ea925dfc42ab50842bb70cd4528253c60c1f99581a436402a0f495e
```

The current Skill has no frontmatter. During the authorized migration operation, prepend the approved canonical frontmatter:

```yaml
---
name: home-studio-3d
description: Home Studio 3D project guidance for canonical context and task routing.
---
```

The existing legacy Skill body must remain byte-for-byte identical after the frontmatter prefix. Do not introduce an unspecified extra blank line or other separator that changes the accepted byte layout. Verify the legacy body digest before the operation, the complete migrated digest after it, and byte equality of the body. The expected complete migrated digest is:

```text
0fdb73131da8875ebe2fd5144da874d2a77f46edd7cf736684dc4a477c6e5ea1
```

## Home task and capability contracts

The six existing task IDs remain unchanged:

1. `project-documentation-read`
2. `slice-007-read-only-verification`
3. `slice-007-controlled-regeneration`
4. `slice-007-live-mcp-verification`
5. `slice-007-protected-promotion`
6. `offline-reentry`

There is no new task DSL and no task-contract redesign. The existing capability architecture, including `blender-cli` and `blender-mcp`, remains unchanged. Machine bindings do not belong in Git. This reconciliation performs no capability installation, Doctor repair, Blender activity, or MCP activity.

## Native evidence and fallback

The accepted P06-GAP-004 repository-backed conclusions and the human-approved P06-GAP-005 discovery conclusion remain in force. P06-GAP-005 is a conversational discovery checkpoint, not a Git document. Canonical Project Skill frontmatter is mandatory. Genuine Codex native provider attestation must not be claimed without genuine evidence. Structural or synthetic receipt data is not native provenance, and synthetic native receipts are not acceptable proof.

The verified Canonical Handoff fallback is sufficient only when Bootstrap is current, PSC is current, Preflight is non-blocked, exact Skill bytes and digest are current, native failure or unavailability is explicit, and Canonical Handoff bindings are verified. A proven fallback produces `READY-WITH-WARNINGS`; an unproven fallback remains `BLOCKED`.

## Activation driver and lock boundary

Stack 1.1.0 `installSnapshot` installs and activates a snapshot; it is not an inactive-installation primitive. Therefore Block 1 must not call `installSnapshot` and must not call `sync:snapshot` for the 1.1.0 candidate. `sync:snapshot` is intentionally not used for this MAJOR transition because its supported result is `major-migration-required`.

After the preparation checkpoint, Block 2 uses the existing verified Stack 1.1.0 internal `installSnapshot` primitive through a purpose-built, one-shot migration driver. The driver is migration-specific scaffolding, not a new public Stack command or permanent migration framework. It imports the primitive from the verified project-local Stack 1.1.0 snapshot/runtime, operates on the explicit Home project root, consumes the already verified inactive candidate, and is disposable unless execution-time evidence separately authorizes tracking it. It must not modify canonical Stack. The exact project-local module path, export, arguments, lock-token semantics, and candidate expectations must be verified against the installed 1.1.0 payload immediately before writing the driver; this document does not fabricate those details.

## Activation ordering

After the preparation checkpoint and explicit activation authorization, one controlled `withProjectLock` scope must cover the authority transition from baseline verification through pin/active coherence:

1. Acquire the project lock using the existing `withProjectLock` primitive or its canonical equivalent.
2. Reverify the coherent 0.4.0 baseline.
3. Reverify the inactive 1.1.0 candidate and its checksums.
4. Use the existing verified `installSnapshot` primitive through the one-shot driver, passing the held lock token where the actual API supports it, to activate the verified 1.1.0 snapshot and checksums.
5. Verify the active snapshot is 1.1.0.
6. Explicitly edit the project-owned `.ai-stack/manifest.json`, changing only `stackVersion` from 0.4.0 to 1.1.0. This is not a Stack manifest-write callable.
7. Verify pin/active coherence as 1.1.0/1.1.0. The interval with active 1.1.0 and pin 0.4.0 is fail-closed and not usable. Release the authority-transition lock only after coherence is established.
8. Run fresh Bootstrap after the authority transition is coherent.
9. Generate fresh PSC.
10. Run Preflight for `project-documentation-read`.
11. Validate a session using genuine native evidence when available, otherwise the verified fallback.

The exact callable names and signatures of these existing primitives must be rechecked against the canonical Stack and Home code at execution time. This design does not introduce a new atomic MAJOR migration command.

The first post-migration task used for session validation is `project-documentation-read`; Blender and MCP are not required for that validation.

## Rollback

If activation or session validation fails, productive Plan 06 work does not continue. Under the appropriate project lock, activate or re-activate the verified 0.4.0 snapshot using the approved rollback mechanism, explicitly restore `.ai-stack/manifest.json` to `stackVersion: 0.4.0` if the pin advanced, and verify both `active = 0.4.0` and `pin = 0.4.0` plus the restored active snapshot. The rollback primitive does not edit the manifest; that project-owned edit is a separate controlled rollback step. A failed or new PSC is not authority. Rollback must not use destructive reset/clean behavior.

## Home contract-test transition

The migration-sensitive Home test is `tests/plan_06/test_project_contract.py`. It currently asserts 0.4.0 authority and must not be changed during preparation. Commit 1 keeps those assertions intact and green because inactive 1.1.0 staging does not change active authority. After authorized activation, Commit 2 updates only the test expectations justified by the verified 1.1.0 candidate: Stack version 1.1.0, runtime path `.ai-stack/runtime/versions/1.1.0/`, canonical snapshot/checksums identities, canonical payload/checksum evidence of 200 and the verified tree evidence, and active authority 1.1.0. The exact test assertions and any structural checksum-file count must be inspected at execution time rather than expanded by assumption. The project-contract tests must be green after both commits.

## Offline proof

Final offline proof means runtime operation from the Home repository, the verified project-local Stack 1.1.0 snapshot, and machine-owned permitted capabilities without dependence on the central Stack checkout, GitHub, the Internet, external `NODE_PATH`, or host `node_modules`.

Candidate construction may use the canonical materializer’s permitted dependency preparation mechanism, including network or cache where required. That construction allowance must not be described as an offline-construction guarantee. The installed runtime’s offline autonomy is the contract.

## Slice 007 boundary

Migration does not modify Slice 007 authority. It performs no Blender regeneration, MCP operation, canonical `.blend` overwrite, protected promotion, or Slice 008 work.

## Scope exclusions

This design does not authorize manifest mutation, Skill mutation, snapshot installation, activation, Bootstrap, PSC creation, Preflight, session start, machine-binding changes, Blender/MCP activity, protected promotion, offline-reentry execution, or Plan 06 Block 4 resumption. Those actions belong to the separately authorized implementation blocks and human checkpoints described in the implementation plan.
