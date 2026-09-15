# Proportional Agentic Execution Policy

## Status and scope

This document is the canonical, shared policy for proportional agentic execution in projects that consume `ai-development-stack`. It applies equally to Claude Code, Codex, Gemini CLI, Antigravity, and other supported agent surfaces.

The policy uses vendor-neutral roles and workflow concepts. It does not prescribe provider-specific commands, configuration, or orchestration features. It governs execution granularity and coordination; the authority, security, repository-boundary, and versioning rules remain defined by the other canonical architecture documents.

## Default execution shape

For a bounded change, use this default sequence:

1. One coherent implementation of the approved scope.
2. One independent review of the complete diff against the requirements.
3. One grouped round of corrections for the review findings.
4. One final verification using the applicable tests, checks, and still-valid evidence.

This sequence is the normal unit of execution. It should be adapted only when a technical reason makes the default shape insufficient.

## Proportional granularity

Do not automatically assign an independent subagent or worker to every microtask. Group related work when it shares the same requirements, files, reasoning, or validation boundary. Use independent workers only when separation provides a concrete technical benefit, such as genuine parallelism, isolation, or a distinct expertise boundary.

Do not chain complete implementation, review, and correction rounds without a technical need. A new round must be justified by new evidence, a changed requirement, a previously undiscovered dependency, or a material correctness, security, or scope concern.

## Human escalation gate

After the first grouped correction round, stop and summarize the current state before continuing if any of the following is needed:

- another integral review of the full change;
- a redesign of the approach; or
- another substantial round of implementation or corrections.

The summary must identify the completed work, remaining findings, relevant evidence, unresolved risks, and the proposed next action. Continuing requires explicit human authorization.

## Review focus and evidence reuse

Reviewers must prioritize, in order of practical relevance:

1. the complete diff;
2. the stated requirements and acceptance criteria; and
3. only the additional context needed to resolve a concrete question.

Reviewers should not repeatedly reread unaffected areas unless a technical dependency, regression risk, or requirement makes that necessary.

Validation evidence remains reusable while its inputs and assumptions remain valid. Do not repeat expensive analysis or tests merely to repeat them; rerun them when the change, environment, evidence, or risk profile gives a technical reason to do so.

## Checkpoints for large plans

For a large plan, divide the work into functional blocks and use a human checkpoint between blocks. The checkpoint should confirm the state, evidence, scope, and next block before autonomous execution continues. Do not execute an entire large plan from beginning to end without those checkpoints.

## Technical exceptions

Exceptions to this policy are allowed when technically justified by correctness, security, isolation, dependency ordering, unavailable evidence, or another material constraint. The reason and the affected scope should be recorded in the work summary. An exception is a bounded response to a specific need; it must not become the default workflow.

## Non-duplication and portability

This policy is the single shared source for proportional execution guidance. README files, surface adapters, project skills, and historical plans must not copy these rules. They may reference this policy and add only local information that does not restate or weaken it.

