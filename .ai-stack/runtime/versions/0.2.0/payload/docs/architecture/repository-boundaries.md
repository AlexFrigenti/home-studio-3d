# Repository and State Boundaries

## Central stack ownership

The canonical `ai-development-stack` repository owns:

- shared, vendor-neutral methodology and guarantees;
- versioned contract schemas and their validation fixtures;
- immutable common snapshot source material and release metadata;
- specifications and architecture policy for distribution and consumption; and
- later, shared development-time lifecycle tooling whose scope is explicitly approved by its own plan.

It does not own project product code, project-specific workflows, project credentials, machine configuration, or live runtime state. Projects consume released snapshots and never depend on the central repository at runtime.

## Project repository ownership

Each configured project owns:

- its source code, tests, product documentation, and delivery workflow;
- its manifest and exact pinned `ai-development-stack` SemVer version;
- its canonical project skill and project-specific agent guidance;
- its declarations of `REQUIRED`, `RECOMMENDED`, and `OPTIONAL` capabilities;
- its materialized copy of the pinned common snapshot; and
- its project-local, non-secret records needed to verify configuration.

Project rules may specialize workflows but may not weaken common security, authority, exact-pinning, validation, or zero-secret guarantees. Volatile project facts are verified from current project state rather than copied into the central stack.

## Machine-local ownership

Machine-local state owns:

- installed executable locations and detected versions;
- capability availability and health observations;
- user-specific paths and operating-system integration;
- authentication sessions and approved secret-store references;
- caches, temporary files, and local logs; and
- local authorization or policy state that must not be committed.

Machine-local state is replaceable and must not become the sole authority for canonical contracts or project instructions. No reusable secret value may flow into a repository, snapshot, adapter, or Project Session Context.

## Boundary interactions

The central stack publishes an immutable versioned snapshot. A project chooses an exact version, validates it, and materializes it locally. Machine-local detection reports whether declared capabilities can be used on the current machine. Project Session Context combines these inputs while preserving the authority order; it does not transfer ownership among them.

Surface adapters remain thin: they expose project-owned context to Claude Code, Codex App, Codex CLI, Antigravity, Antigravity IDE, or Gemini CLI. They do not become stores of shared knowledge or project policy.

## Foundation boundary

Foundation is documentation and declarative contract groundwork only. It does not create `runtime/`, `bootstrap/`, `doctor/`, `sync/`, `rollback/`, `state/`, or `adapters/`; it does not implement checksums or update behavior; and it does not modify `home-studio-3d`. Those responsibilities are reserved for later plans.
