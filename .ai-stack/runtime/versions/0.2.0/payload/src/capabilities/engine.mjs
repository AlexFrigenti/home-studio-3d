import { fingerprintSafeInputs, sanitizeEvidence } from "./evidence.mjs";

function reasonFor(check, observation, result) {
  if (observation?.reasonCode) return observation.reasonCode;
  if (result === "unknown") return "DRIVER_FAILURE";
  if (result === "fail") return "CHECK_FAILED";
  return undefined;
}

function observationAt(observations, check, index) {
  if (!Array.isArray(observations)) return undefined;
  const keyed = observations.find((observation) => observation?.checkId === check.id || observation?.id === check.id);
  return keyed ?? observations[index];
}

function buildCheckState(check, observation, now) {
  const observedAt = now();
  if (!(observedAt instanceof Date) || Number.isNaN(observedAt.valueOf())) throw new TypeError("invalid clock");
  const observedAtText = observedAt.toISOString();
  const validUntil = new Date(observedAt.valueOf() + check.freshness.maxAgeSeconds * 1000).toISOString();
  const sanitized = sanitizeEvidence(check, observation?.evidence ?? {});
  const malformedStatus = !["pass", "fail", "unknown"].includes(observation?.status);
  const result = malformedStatus || sanitized.invalid ? "unknown" : observation.status;
  const reasonCode = malformedStatus
    ? "DRIVER_FAILURE"
    : sanitized.invalid
      ? "EVIDENCE_INVALID"
      : reasonFor(check, observation, result);
  const record = {
    id: check.id,
    importance: check.importance,
    result,
    observedAt: observedAtText,
    validUntil,
    fingerprint: fingerprintSafeInputs(observation?.fingerprintInputs ?? sanitized.evidence)
  };
  if (Object.keys(sanitized.evidence).length > 0) record.evidence = sanitized.evidence;
  if (reasonCode) record.reasonCode = reasonCode;
  return record;
}

export function evaluateCapability({ definition, surface, observations, now }) {
  const checks = definition.checks.map((check, index) => buildCheckState(check, observationAt(observations, check, index), now));
  const essential = checks.filter((check) => check.importance === "essential");
  const auxiliary = checks.filter((check) => check.importance === "auxiliary");
  const essentialUnknown = essential.some((check) => check.result === "unknown");
  const essentialFailure = essential.some((check) => check.result === "fail");
  const auxiliaryUnknown = auxiliary.some((check) => check.result === "unknown");
  const auxiliaryFailure = auxiliary.some((check) => check.result === "fail");
  let state = "available";
  if (essentialUnknown) state = "unknown";
  else if (essentialFailure) state = "unavailable";
  else if (auxiliaryUnknown) state = "unknown";
  else if (auxiliaryFailure) state = "degraded";
  const reasons = checks
    .filter((check) => check.result !== "pass")
    .map((check) => ({ code: check.reasonCode ?? "CHECK_FAILED", checkId: check.id }));
  return { capability: definition.id, surface, state, checks, reasons };
}

function fallbackReason(evaluation) {
  if (evaluation.reasons?.length > 0) return evaluation.reasons[0];
  return { code: evaluation.state === "unknown" ? "CAPABILITY_UNKNOWN_STATE" : "CAPABILITY_UNAVAILABLE" };
}

export function evaluateRequirement({ evaluation, requirement, degradedPolicy }) {
  const sufficient = evaluation.state === "available"
    || (evaluation.state === "degraded" && degradedPolicy === "allow-with-warning");
  const reason = fallbackReason(evaluation);
  const blockers = requirement.level === "REQUIRED" && !sufficient ? [reason] : [];
  const warnings = requirement.level === "RECOMMENDED" && !sufficient ? [reason] : [];
  return {
    capability: evaluation.capability,
    surface: evaluation.surface,
    requirement: requirement.level,
    state: evaluation.state,
    sufficient,
    reasons: structuredClone(evaluation.reasons ?? []),
    blockers,
    warnings,
    suggestedRepairIds: [],
    provenance: []
  };
}
