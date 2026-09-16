import { SURFACES } from "../capabilities/constants.mjs";

export const SESSION_STATUSES = Object.freeze(["ready", "ready-with-warnings", "blocked"]);
export const HANDOFF_STATUSES = Object.freeze(["materialized", "blocked"]);
export const MATERIALIZATION_OUTCOMES = Object.freeze([
  "materialized",
  "unavailable",
  "incompatible",
  "drift"
]);
export const MATERIALIZATION_MECHANISMS = Object.freeze(["native", "universal-fallback"]);
export const REASON_CATEGORIES = Object.freeze([
  "native-integration",
  "context-state",
  "capability",
  "integrity-security"
]);
export const GUARANTEES = Object.freeze([
  "bootstrap",
  "snapshot",
  "psc",
  "preflight",
  "project-skill",
  "context",
  "handoff",
  "authorization",
  "session"
]);
export const CONTEXT_KINDS = Object.freeze(["psc", "project-skill", "preflight", "document"]);
export const PSC_REFERENCE = ".ai-stack/state/project-session-context.json";
export const ACTIVE_CHECKSUMS_REFERENCE = ".ai-stack/checksums.json";
export const PREFLIGHT_REFERENCE = "contract:preflight";
export const SHA256_PATTERN = /^[a-f0-9]{64}$/;
export const SEMVER_PATTERN = /^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$/;
export const REASON_CODE_PATTERN = /^[A-Z][A-Z0-9_]*$/;
export const CONTEXT_REASON_CODE_PATTERN = /^[a-z][a-z0-9-]{0,63}$/;

export { SURFACES };
