# Authority Model

## Purpose

This document defines how every supported agent resolves conflicts and uncertainty while working in a project configured with `ai-development-stack`. The order is mandatory and applies equally online and offline.

## Authority order

From highest to lowest authority:

1. **Security constraints and current human authorization.** Platform safety controls, least-privilege limits, and the user's current authorization bound every action. Authorization for one action does not imply authorization for a broader or destructive action.
2. **Verifiable repository state.** Tracked files, current commits, diffs, executable test results, and other directly inspectable repository evidence outrank descriptions of what the repository is expected to contain.
3. **Current project documentation.** Documentation in the active project governs project intent and maintained procedures when it agrees with verifiable state.
4. **Canonical project skill.** The one project-owned canonical skill provides task routing and project-specific operating guidance without replacing repository evidence or documentation.
5. **Pinned common snapshot.** The exact SemVer snapshot supplies shared contracts, guarantees, and methodology when higher project-specific authorities do not override it.
6. **Agent inference.** Inference may bridge harmless gaps only. It is never evidence and cannot authorize actions or override any higher source.

## Conflict handling

An agent must use the highest applicable authority and record or report a material conflict. If the conflict affects safety, correctness, external state, or scope, the agent stops before the affected action and seeks human direction. It must not silently merge contradictory instructions or treat absence of evidence as authorization.

Repository state is “verifiable” only when observed in the active checkout or by an approved authoritative tool. Cached summaries and remembered facts are not equivalent. Volatile facts must be re-read from their authoritative source when needed.

## Authorization and capabilities

A capability declaration expresses project intent, not human consent and not proof that the capability is available. `REQUIRED`, `RECOMMENDED`, and `OPTIONAL` levels cannot override security controls or authorize installation, authentication, network access, destructive changes, or external writes.

No authority level permits secrets to be committed to the central stack, snapshots, project documentation, project skills, manifests, adapters, or generated session context. Secrets remain in approved machine-local stores.

## Session application

Project Session Context must preserve the source and precedence of included information. Thin adapters may select or format context for a surface, but may not reorder authorities, conceal conflicts, or promote agent inference. When offline, the same order applies using the project-local pinned snapshot and currently verifiable local state.
