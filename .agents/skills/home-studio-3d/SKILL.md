# Home Studio 3D Project Skill

Use this project skill as stable routing guidance for Home Studio 3D work.

## Authority and context

- `measurements/` is the architectural source of truth; Blender scenes are derived representations.
- Start with the current PSC, canonical Preflight, this skill, `AGENTS.md`, and `PROJECT_CONTEXT.md`.
- Read `README.md`, `CONTRIBUTING.md`, `.quality/QUALITY.md`, and the decision records only when the task needs them.
- For Slice 007 work, read the declared active slice `spec.md`, `plan.md`, and `tasks.md` when the task requires those details.
- Keep context selection limited to declared documents and the reason for the current task.

## Task intents

- `project-documentation-read`: inspect project correspondence without Blender interaction.
- `slice-007-read-only-verification`: inspect the existing Slice 007 derived state and authority chain.
- `slice-007-controlled-regeneration`: create an isolated, non-authoritative Slice 007 derivative.
- `slice-007-live-mcp-verification`: perform explicitly requested live Blender MCP work.
- `slice-007-protected-promotion`: handle a validated pilot derivative at its protected boundary.
- `offline-reentry`: re-enter a prepared project using its local verified Stack payload.

## Safety boundaries

- Blender CLI and live MCP are task-scoped declarations in the project manifest; this skill never changes their levels.
- A live MCP task does not silently fall back to CLI.
- `ready` describes evaluated prerequisites; it does not permit a protected action.
- Preserve existing measurements, Slice 007 authorities, and project decisions. Use isolated reversible outputs for pilot work.
