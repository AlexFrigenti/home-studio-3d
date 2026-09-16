import { createHash } from "node:crypto";

import { fingerprintSafeInputs, sanitizeEvidence } from "./evidence.mjs";

const FINGERPRINT = /^[a-f0-9]{64}$/;

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort((left, right) => left.localeCompare(right))
        .map((key) => [key, canonicalize(value[key])])
    );
  }
  return value;
}

function digest(value) {
  return createHash("sha256")
    .update(JSON.stringify(canonicalize(value)), "utf8")
    .digest("hex");
}

export function primitiveContractIdentity(primitive) {
  if (!primitive || typeof primitive !== "object") return undefined;
  return digest({
    id: primitive.id,
    driver: primitive.driver,
    targetClass: primitive.targetClass,
    effect: primitive.effect,
    preflightAllowed: primitive.preflightAllowed,
    timeoutMs: primitive.timeoutMs,
    importance: primitive.importance,
    evidence: primitive.evidence,
    freshness: primitive.freshness,
    configSchema: primitive.configSchema,
    degradedPolicyContribution: primitive.degradedPolicyContribution
  });
}

export function definitionDigestForCapability(capability) {
  if (!capability || typeof capability !== "object") throw new TypeError("capability definition required");
  return digest({
    id: capability.id,
    surfaces: [...(capability.surfaces ?? [])],
    checks: (capability.checks ?? []).map((check) => ({
      id: check.id,
      primitiveId: check.primitiveId,
      symbolicTarget: check.symbolicTarget,
      targetClass: check.targetClass,
      config: check.config,
      primitiveContractIdentity: check.primitiveContractIdentity
    }))
  });
}

export function fingerprintInputsForCheck(check, surface, overrides, identity = {}) {
  const inputs = {};
  for (const input of check?.freshness?.fingerprintInputs ?? []) {
    if (input === "binding" && identity.bindingFingerprint !== undefined) {
      inputs[input] = identity.bindingFingerprint;
    } else if (input === "binding" && identity.bindingStatus !== undefined) {
      inputs[input] = `binding:${identity.bindingStatus}`;
    } else {
      inputs[input] = overrides?.[input] ?? `${surface}:${input}`;
    }
  }
  const projectIdentity = check?.primitiveId !== undefined || check?.definitionDigest !== undefined;
  if (projectIdentity || identity.snapshotIdentity !== undefined) {
    if (check?.definitionDigest !== undefined) inputs.definitionDigest = check.definitionDigest;
    if (check?.primitiveId !== undefined) inputs.primitiveId = check.primitiveId;
    if (check?.targetClass !== undefined) inputs.targetClass = check.targetClass;
    if (check?.symbolicTarget !== undefined) inputs.symbolicTarget = check.symbolicTarget;
    if (check?.primitiveContractIdentity !== undefined) {
      inputs.primitiveContractIdentity = check.primitiveContractIdentity;
    }
    if (identity.primitiveContractIdentity !== undefined) {
      inputs.primitiveContractIdentity = identity.primitiveContractIdentity;
    }
    if (identity.snapshotIdentity !== undefined) inputs.snapshotIdentity = identity.snapshotIdentity;
    if (identity.taskIds !== undefined) {
      inputs.taskSelection = [...identity.taskIds].sort((left, right) => left.localeCompare(right)).join(",");
    }
  }
  if (identity.bindingFingerprint !== undefined && !Object.hasOwn(inputs, "binding")) {
    inputs.bindingFingerprint = identity.bindingFingerprint;
  }
  return inputs;
}

export function fingerprintForCheck(check, surface, overrides, identity) {
  return fingerprintSafeInputs(fingerprintInputsForCheck(check, surface, overrides, identity));
}

export function isEvidenceFresh(record, { check, now, currentFingerprint } = {}) {
  try {
    if (!record || !check || typeof now !== "function" || typeof currentFingerprint !== "string") return false;
    if (record.id !== check.id || !FINGERPRINT.test(record.fingerprint) || record.fingerprint !== currentFingerprint) return false;
    if (!["pass", "fail", "unknown"].includes(record.result)) return false;
    const observedAt = Date.parse(record.observedAt);
    const validUntil = Date.parse(record.validUntil);
    const current = now();
    if (!Number.isFinite(observedAt) || !Number.isFinite(validUntil) || !(current instanceof Date) || Number.isNaN(current.valueOf())) return false;
    if (validUntil <= observedAt || validUntil - observedAt > check.freshness.maxAgeSeconds * 1000) return false;
    if (current.valueOf() < observedAt || current.valueOf() >= validUntil) return false;
    return !sanitizeEvidence(check, record.evidence ?? {}).invalid;
  } catch {
    return false;
  }
}
