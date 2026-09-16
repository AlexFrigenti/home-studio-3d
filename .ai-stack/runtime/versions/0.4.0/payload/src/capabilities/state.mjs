import path from "node:path";

import { loadCapabilityValidators } from "./schema.mjs";
import { CapabilityError } from "./errors.mjs";
import { assertSafeTarget, DEFAULT_FILE_SYSTEM } from "./safe-paths.mjs";
import { SURFACES } from "./constants.mjs";

const STATE_SCHEMA_VERSION = 1;
const SAFE_EVIDENCE_KEYS = new Set(["present", "registered", "reachable", "authenticated", "version", "fingerprint"]);
const IDENTIFIER = /^[a-z][a-z0-9-]*$/;
const REASON_CODE = /^[A-Z][A-Z0-9_]*$/;
const EXACT_VERSION = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
const FINGERPRINT = /^[a-f0-9]{64}$/;

function invalidState() {
  throw new CapabilityError("CAPABILITY_STATE_INVALID");
}

function copyEvidence(evidence) {
  if (evidence === undefined) return undefined;
  if (!evidence || typeof evidence !== "object" || Array.isArray(evidence)) invalidState();
  const safe = {};
  for (const [key, value] of Object.entries(evidence)) {
    if (!SAFE_EVIDENCE_KEYS.has(key)) continue;
    const valid = key === "version"
      ? typeof value === "string" && EXACT_VERSION.test(value)
      : key === "fingerprint"
        ? typeof value === "string" && FINGERPRINT.test(value)
        : key === "authenticated"
          ? typeof value === "boolean" || value === "unknown"
          : typeof value === "boolean";
    if (!valid) invalidState();
    safe[key] = value;
  }
  return Object.keys(safe).length > 0 ? safe : undefined;
}

function copyCheck(check) {
  if (!check || typeof check !== "object" || Array.isArray(check)
    || typeof check.id !== "string" || !IDENTIFIER.test(check.id)
    || !["essential", "auxiliary"].includes(check.importance)
    || !["pass", "fail", "unknown"].includes(check.result)
    || typeof check.observedAt !== "string"
    || typeof check.validUntil !== "string") invalidState();
  const safe = {
    id: check.id,
    importance: check.importance,
    result: check.result,
    observedAt: check.observedAt,
    validUntil: check.validUntil
  };
  if (check.reasonCode !== undefined) {
    if (typeof check.reasonCode !== "string" || !REASON_CODE.test(check.reasonCode)) invalidState();
    safe.reasonCode = check.reasonCode;
  }
  const evidence = copyEvidence(check.evidence);
  if (evidence) safe.evidence = evidence;
  if (check.fingerprint !== undefined) {
    if (typeof check.fingerprint !== "string" || !FINGERPRINT.test(check.fingerprint)) invalidState();
    safe.fingerprint = check.fingerprint;
  }
  return safe;
}

function copyEvaluation(evaluation) {
  if (!evaluation || typeof evaluation !== "object" || Array.isArray(evaluation)
    || typeof evaluation.capability !== "string" || !IDENTIFIER.test(evaluation.capability)
    || !SURFACES.includes(evaluation.surface)
    || !["available", "degraded", "unavailable", "unknown"].includes(evaluation.state)
    || !Array.isArray(evaluation.checks)
    || !Array.isArray(evaluation.reasons)) invalidState();
  return {
    capability: evaluation.capability,
    surface: evaluation.surface,
    state: evaluation.state,
    checks: evaluation.checks.map(copyCheck),
    reasons: evaluation.reasons.map(({ code, checkId }) => {
      if (typeof code !== "string" || !REASON_CODE.test(code)
        || (checkId !== undefined && (typeof checkId !== "string" || !IDENTIFIER.test(checkId)))) {
        invalidState();
      }
      return checkId === undefined ? { code } : { code, checkId };
    })
  };
}

function assertBasicState(state) {
  if (!state || state.schemaVersion !== STATE_SCHEMA_VERSION || typeof state.observedAt !== "string" || !Array.isArray(state.capabilities)) {
    throw new CapabilityError("CAPABILITY_STATE_INVALID");
  }
}

export function createCapabilityState({ observedAt, evaluations }) {
  const state = {
    schemaVersion: STATE_SCHEMA_VERSION,
    observedAt,
    capabilities: evaluations.map(copyEvaluation)
  };
  assertBasicState(state);
  return state;
}

export function serializeCapabilityState(state) {
  assertBasicState(state);
  return Buffer.from(`${JSON.stringify(state, null, 2)}\n`, "utf8");
}

export async function readCapabilityState(projectRoot, { fileSystem = DEFAULT_FILE_SYSTEM } = {}) {
  const destination = path.join(projectRoot, ".ai-stack", "state", "capabilities.json");
  fileSystem = { ...DEFAULT_FILE_SYSTEM, ...fileSystem };
  let bytes;
  try {
    await assertSafeTarget(destination, fileSystem);
    bytes = await fileSystem.readFile(destination);
  } catch (error) {
    if (error?.code === "ENOENT") return undefined;
    throw new CapabilityError("CAPABILITY_STATE_INVALID");
  }
  try {
    const state = JSON.parse(bytes.toString("utf8"));
    const validators = await loadCapabilityValidators();
    if (!validators.validateCapabilityState(state)) throw new Error("invalid capability state");
    return state;
  } catch (error) {
    if (error instanceof CapabilityError) throw error;
    throw new CapabilityError("CAPABILITY_STATE_INVALID");
  }
}
