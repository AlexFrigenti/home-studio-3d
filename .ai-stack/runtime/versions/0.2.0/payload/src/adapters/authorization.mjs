import { AdapterError, adapterReason } from "./errors.mjs";
import { SHA256_PATTERN, SURFACES } from "./constants.mjs";

const REQUIREMENT_KEYS = ["operation", "scope", "preconditionDigest", "validUntil"];
const EVIDENCE_KEYS = ["authenticated", ...REQUIREMENT_KEYS];

function hasExactKeys(value, keys) {
  return Boolean(
    value
    && typeof value === "object"
    && !Array.isArray(value)
    && Object.keys(value).length === keys.length
    && keys.every((key) => Object.hasOwn(value, key))
  );
}

function isBoundedString(value) {
  return typeof value === "string" && value.length > 0 && value.length <= 128;
}

function isValidDigest(value) {
  return typeof value === "string" && SHA256_PATTERN.test(value);
}

function isValidDate(value) {
  return typeof value === "string" && Number.isFinite(Date.parse(value));
}

function reason(code, safeDetails = {}) {
  return adapterReason({
    code,
    category: "integrity-security",
    guarantee: "authorization",
    safeDetails
  });
}

function blocked(reasons) {
  return { status: "blocked", reasons };
}

export function verifyNativeAuthorization({ requirement, evidence, currentInputDigest } = {}) {
  const reasons = [];
  if (!hasExactKeys(requirement, REQUIREMENT_KEYS)) {
    reasons.push(reason("AUTHORIZATION_REQUIREMENT_INVALID"));
  }
  if (!hasExactKeys(evidence, EVIDENCE_KEYS)) {
    reasons.push(reason("AUTHORIZATION_EVIDENCE_INVALID"));
  }
  if (
    !hasExactKeys(requirement, REQUIREMENT_KEYS)
    || !isBoundedString(requirement.operation)
    || !isBoundedString(requirement.scope)
    || !isValidDigest(requirement.preconditionDigest)
    || !isValidDate(requirement.validUntil)
  ) {
    reasons.push(reason("AUTHORIZATION_REQUIREMENT_INVALID"));
  }
  if (
    !hasExactKeys(evidence, EVIDENCE_KEYS)
    || ![true, false, "unknown"].includes(evidence.authenticated)
    || !isBoundedString(evidence.operation)
    || !isBoundedString(evidence.scope)
    || !isValidDigest(evidence.preconditionDigest)
    || !isValidDate(evidence.validUntil)
  ) {
    reasons.push(reason("AUTHORIZATION_EVIDENCE_INVALID"));
  }
  if (!isValidDigest(currentInputDigest)) {
    reasons.push(reason("AUTHORIZATION_INPUT_INVALID"));
  }
  if (reasons.length > 0) return blocked(reasons);

  if (evidence.operation !== requirement.operation) {
    reasons.push(reason("AUTHORIZATION_OPERATION_MISMATCH", { actual: evidence.operation }));
  }
  if (evidence.scope !== requirement.scope) {
    reasons.push(reason("AUTHORIZATION_SCOPE_MISMATCH", { actual: evidence.scope }));
  }
  if (evidence.preconditionDigest !== requirement.preconditionDigest) {
    reasons.push(reason("AUTHORIZATION_PRECONDITION_MISMATCH"));
  }
  if (currentInputDigest !== requirement.preconditionDigest) {
    reasons.push(reason("AUTHORIZATION_INPUT_MISMATCH"));
  }
  if (evidence.validUntil !== requirement.validUntil) {
    reasons.push(reason("AUTHORIZATION_VALIDITY_MISMATCH"));
  }

  const now = Date.now();
  if (Date.parse(requirement.validUntil) <= now || Date.parse(evidence.validUntil) <= now) {
    reasons.push(reason("AUTHORIZATION_EXPIRED"));
  }
  if (evidence.authenticated === "unknown") {
    reasons.push(reason("AUTHORIZATION_UNKNOWN"));
  } else if (evidence.authenticated !== true) {
    reasons.push(reason("AUTHORIZATION_INSUFFICIENT"));
  }

  return reasons.length > 0 ? blocked(reasons) : { status: "sufficient", reasons: [] };
}

export async function executeCanonicalAction({
  surface,
  requirement,
  evidence,
  currentInputDigest,
  action
} = {}) {
  if (!SURFACES.includes(surface)) {
    return blocked([reason("SURFACE_IDENTITY_INVALID", { surface })]);
  }
  if (typeof action !== "function") {
    throw new TypeError("action must be a function");
  }

  if (requirement === undefined || requirement === null) {
    return { status: "sufficient", reasons: [], result: await action() };
  }

  const authorization = verifyNativeAuthorization({
    requirement,
    evidence,
    currentInputDigest
  });
  if (authorization.status !== "sufficient") return authorization;

  return { ...authorization, result: await action() };
}
