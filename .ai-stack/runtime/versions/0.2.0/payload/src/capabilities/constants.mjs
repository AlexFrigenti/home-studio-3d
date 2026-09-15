export const SURFACES = Object.freeze([
  "claude-code",
  "codex-cli",
  "codex-app",
  "gemini-cli",
  "antigravity-ide",
  "antigravity-desktop"
]);

export const EFFECTS = Object.freeze(["local-read", "local-exec", "network-read"]);
export const CAPABILITY_STATES = Object.freeze(["available", "degraded", "unavailable", "unknown"]);
export const REQUIREMENT_LEVELS = Object.freeze(["REQUIRED", "RECOMMENDED", "OPTIONAL"]);
export const DRIVER_IDS = Object.freeze([
  "executable",
  "version",
  "file-config",
  "mcp",
  "authentication",
  "network"
]);

export const CAPABILITY_ID_PATTERN = /^[a-z][a-z0-9-]*$/;
